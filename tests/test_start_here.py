"""Run the copy-paste code in START_HERE.md against a local fake Lago API."""

from __future__ import annotations

import base64
import hashlib
import hmac
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START_HERE = ROOT / "START_HERE.md"
BLOCK = re.compile(r"^```\w+ file=(?P<name>[\w.-]+)\n(?P<body>.*?)^```$", re.M | re.S)
API_KEY = "test-key-not-a-secret"
HMAC_KEY = "test-hmac-key"


def code_blocks() -> dict[str, str]:
    return {match["name"]: match["body"] for match in BLOCK.finditer(START_HERE.read_text(encoding="utf-8"))}


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


class FakeLago:
    """Implements the endpoints START_HERE.md calls, with Postgres duplicate semantics."""

    def __init__(self, public_key_pem: str):
        self.public_key_pem = public_key_pem
        self.requests: list[tuple[str, str, object]] = []
        self.events: dict[str, dict] = {}
        self.fail_next_event_with_503 = False
        handler = self._handler()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()

    def _handler(self):
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _send(self, status, body=None):
                data = b"" if body is None else json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _route(self, method):
                if self.headers.get("Authorization") != f"Bearer {API_KEY}":
                    return self._send(401, {"status": 401, "error": "Unauthorized"})
                length = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(length)) if length else None
                path = self.path
                fake.requests.append((method, path, body))
                if method == "POST" and path == "/api/v1/customers":
                    return self._send(200, {"customer": body["customer"]})
                if method == "POST" and path == "/api/v1/subscriptions":
                    return self._send(200, {"subscription": body["subscription"]})
                if method == "POST" and path == "/api/v1/events":
                    if fake.fail_next_event_with_503:
                        fake.fail_next_event_with_503 = False
                        return self._send(503, {"status": 503, "error": "Service Unavailable"})
                    event = body["event"]
                    if event["code"] == "__contract_error__":
                        return self._send(422, {"status": 422, "error": "Unprocessable Entity", "code": "validation_errors",
                                                "error_details": {"code": ["value_is_invalid"]}})
                    if event["transaction_id"] in fake.events:
                        return self._send(422, {"status": 422, "error": "Unprocessable Entity", "code": "validation_errors",
                                                "error_details": {"transaction_id": ["value_already_exist"]}})
                    fake.events[event["transaction_id"]] = event
                    return self._send(200, {"event": event})
                if method == "GET" and path.startswith("/api/v1/customers/cus_1/current_usage?external_subscription_id=sub_1"):
                    tokens = sum(e["properties"]["tokens"] for e in fake.events.values())
                    return self._send(200, {"customer_usage": {"amount_cents": round(tokens * 0.002), "currency": "USD", "charges_usage": [
                        {"units": f"{tokens}.0", "amount_cents": round(tokens * 0.002), "billable_metric": {"code": "llm_tokens"}}]}})
                if method == "GET" and path == "/api/v1/subscriptions/sub_1/entitlements":
                    return self._send(200, {"entitlements": [{"code": "seats", "name": "Seats", "description": None,
                        "privileges": [{"code": "max", "name": "Max", "value_type": "integer", "config": {}, "value": 10,
                                        "plan_value": 10, "override_value": None}], "overrides": {}}]})
                if method == "GET" and path == "/api/v1/wallets?external_customer_id=cus_1":
                    return self._send(200, {"wallets": [{"status": "active", "ongoing_balance_cents": 750},
                                                        {"status": "terminated", "ongoing_balance_cents": 999}], "meta": {}})
                if method == "GET" and path == "/api/v1/webhooks/json_public_key":
                    return self._send(200, {"webhook": {"public_key": base64.b64encode(fake.public_key_pem.encode()).decode()}})
                return self._send(404, {"status": 404, "error": "Not Found", "path": path})

            def do_GET(self):
                self._route("GET")

            def do_POST(self):
                self._route("POST")

        return Handler


@unittest.skipUnless(shutil.which("openssl"), "openssl is required to sign test webhooks")
class StartHereTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blocks = code_blocks()
        cls.tmp = Path(tempfile.mkdtemp(prefix="start-here-"))
        key = cls.tmp / "key.pem"
        subprocess.run(["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(key)],
                       check=True, capture_output=True)
        cls.private_key = key
        cls.public_pem = subprocess.run(["openssl", "pkey", "-in", str(key), "-pubout"], check=True, capture_output=True,
                                        text=True).stdout
        cls.fake = FakeLago(cls.public_pem)

    @classmethod
    def tearDownClass(cls):
        cls.fake.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        self.fake.events.clear()
        self.fake.requests.clear()

    def jwt(self, data: str, issuer: str, alg: str = "RS256") -> str:
        header = b64url(json.dumps({"alg": alg, "typ": "JWT"}).encode())
        payload = b64url(json.dumps({"data": data, "iss": issuer}).encode())
        signed = subprocess.run(["openssl", "dgst", "-sha256", "-sign", str(self.private_key)],
                                input=f"{header}.{payload}".encode(), check=True, capture_output=True).stdout
        return f"{header}.{payload}.{b64url(signed)}"

    def webhook_cases(self):
        body = json.dumps({"webhook_type": "invoice.created", "object_type": "invoice", "invoice": {"lago_id": "inv_1"}})
        good_hmac = base64.b64encode(hmac.new(HMAC_KEY.encode(), body.encode(), hashlib.sha256).digest()).decode()
        return body, [
            ("jwt-valid", body, {"x-lago-signature": self.jwt(body, self.fake.url), "x-lago-signature-algorithm": "jwt"}, True),
            ("jwt-tampered-body", body.replace("inv_1", "inv_2"),
             {"x-lago-signature": self.jwt(body, self.fake.url), "x-lago-signature-algorithm": "jwt"}, False),
            ("jwt-wrong-issuer", body, {"x-lago-signature": self.jwt(body, "https://evil.example"), "x-lago-signature-algorithm": "jwt"}, False),
            ("jwt-alg-none", body, {"x-lago-signature": self.jwt(body, self.fake.url, alg="none"), "x-lago-signature-algorithm": "jwt"}, False),
            ("hmac-valid", body, {"x-lago-signature": good_hmac, "x-lago-signature-algorithm": "hmac"}, True),
            ("hmac-tampered-body", body + " ", {"x-lago-signature": good_hmac, "x-lago-signature-algorithm": "hmac"}, False),
            ("unsigned", body, {}, False),
        ]

    def test_python_client_and_webhooks(self):
        module_path = self.tmp / "lago_billing.py"
        module_path.write_text(self.blocks["lago_billing.py"], encoding="utf-8")
        spec = importlib.util.spec_from_file_location("lago_billing", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        lago = module.Lago(api_url=self.fake.url + "/", api_key=API_KEY, max_retries=2)

        lago.upsert_customer("cus_1", "Acme", "USD")
        self.assertNotIn("email", self.fake.requests[-1][2]["customer"])
        lago.create_subscription("sub_1", "cus_1", "pro")
        self.assertEqual(self.fake.requests[-1][2]["subscription"]["external_customer_id"], "cus_1")

        occurred = datetime(2026, 10, 1, 12, 0, 0, 250000, tzinfo=timezone.utc)
        self.fake.fail_next_event_with_503 = True
        self.assertEqual(lago.send_usage("usage_42", "sub_1", "llm_tokens", occurred, {"tokens": 120000}), "accepted")
        self.assertEqual(lago.send_usage("usage_42", "sub_1", "llm_tokens", occurred, {"tokens": 120000}), "duplicate")
        posted = [body["event"] for method, path, body in self.fake.requests if path == "/api/v1/events"]
        self.assertEqual(len(posted), 3)  # 503, retry, replay
        self.assertEqual({(e["transaction_id"], e["timestamp"]) for e in posted}, {("usage_42", "1790856000.250")})
        self.assertEqual(lago.current_usage("cus_1", "sub_1")["amount_cents"], 240)
        with self.assertRaises(module.LagoError):
            lago.send_usage("usage_43", "sub_1", "__contract_error__", occurred, {"tokens": 1})

        self.assertEqual(lago.entitlement("sub_1", "seats"), {"enabled": True, "privileges": {"max": 10}})
        self.assertEqual(lago.entitlement("sub_1", "sso"), {"enabled": False, "privileges": {}})
        self.assertEqual(lago.prepaid_balance_cents("cus_1"), 750)
        self.assertEqual(lago.webhook_public_key(), self.public_pem)

        has_pyjwt = importlib.util.find_spec("jwt") is not None
        _, cases = self.webhook_cases()
        for name, body, headers, valid in cases:
            if headers.get("x-lago-signature-algorithm") == "jwt" and not has_pyjwt:
                continue
            with self.subTest(name):
                canonical = {k.replace("x-lago", "X-Lago").replace("-signature", "-Signature").replace("-algorithm", "-Algorithm"): v
                             for k, v in headers.items()}
                call = lambda: module.verify_webhook(body.encode(), canonical, issuer=self.fake.url,
                                                     public_key_pem=self.public_pem, hmac_key=HMAC_KEY)
                if valid:
                    self.assertEqual(call()["invoice"]["lago_id"], "inv_1")
                else:
                    with self.assertRaises(Exception):
                        call()

    @unittest.skipUnless(shutil.which("node"), "node is required for the TypeScript example")
    def test_typescript_client_and_webhooks(self):
        version = subprocess.run(["node", "-p", "process.versions.node.split('.').map(Number)"], capture_output=True, text=True)
        major, minor = json.loads(version.stdout.replace("[ ", "[").replace(" ]", "]"))[:2]
        if (major, minor) < (22, 6):
            self.skipTest("Node 22.6+ is required to run TypeScript without a build step")
        (self.tmp / "lago-billing.mts").write_text(self.blocks["lago-billing.ts"], encoding="utf-8")
        route = self.blocks["webhook-route.ts"].replace('"./lago-billing"', '"./lago-billing.mts"')
        (self.tmp / "webhook-route.mts").write_text(route, encoding="utf-8")
        body, cases = self.webhook_cases()
        driver = self.tmp / "driver.mjs"
        driver.write_text(DRIVER, encoding="utf-8")
        env = {"PATH": os.environ["PATH"], "LAGO_API_URL": self.fake.url, "LAGO_API_KEY": API_KEY,
               "LAGO_WEBHOOK_HMAC_KEY": HMAC_KEY, "CASES": json.dumps(cases)}
        result = subprocess.run(["node", "--experimental-strip-types", "--no-warnings", str(driver)], cwd=self.tmp, env=env,
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["first"], "accepted")
        self.assertEqual(report["replay"], "duplicate")
        self.assertEqual(report["contractError"], 422)
        self.assertEqual(report["usageCents"], 240)
        self.assertEqual(report["entitled"], {"enabled": True, "privileges": {"max": 10}})
        self.assertEqual(report["balance"], 750)
        self.assertEqual(report["routeStatuses"], {name: 204 if valid else 401 for name, _, _, valid in cases})
        self.assertEqual(report["inserted"], ["key-jwt-valid", "key-hmac-valid"])
        posted = [body["event"] for method, path, body in self.fake.requests if path == "/api/v1/events"]
        self.assertEqual({(e["transaction_id"], e["timestamp"]) for e in posted if e["code"] == "llm_tokens"},
                         {("usage_42", "1790856000.250")})


DRIVER = r"""
import { configFromEnv, sendUsage, currentUsage, entitlement, prepaidBalanceCents, upsertCustomer, createSubscription, LagoError } from "./lago-billing.mts";
import { makeWebhookHandler } from "./webhook-route.mts";

const config = { ...configFromEnv(), maxRetries: 2 };
await upsertCustomer(config, { id: "cus_1", name: "Acme", currency: "USD" });
await createSubscription(config, { id: "sub_1", customerId: "cus_1", planCode: "pro" });
const record = { id: "usage_42", subscriptionId: "sub_1", metricCode: "llm_tokens", occurredAt: new Date(Date.UTC(2026, 9, 1, 12, 0, 0, 250)), properties: { tokens: 120000 } };
const first = await sendUsage(config, record);
const replay = await sendUsage(config, record);
let contractError = null;
try { await sendUsage(config, { ...record, id: "usage_43", metricCode: "__contract_error__" }); } catch (e) { contractError = e instanceof LagoError ? e.status : String(e); }
const usage = await currentUsage(config, "cus_1", "sub_1");
const entitled = await entitlement(config, "sub_1", "seats");
const balance = await prepaidBalanceCents(config, "cus_1");

const inserted = [];
const seen = new Set();
const inbox = { async insertIfNew(key) { if (seen.has(key)) return false; seen.add(key); return true; } };
const handler = makeWebhookHandler(inbox, async (key) => { inserted.push(key); });
const routeStatuses = {};
for (const [name, body, headers] of JSON.parse(process.env.CASES)) {
  const request = new Request("http://app.test/api/lago/webhooks", { method: "POST", body, headers: { ...headers, "x-lago-unique-key": `key-${name}` } });
  routeStatuses[name] = (await handler(request)).status;
}
const [[, hb, hh]] = JSON.parse(process.env.CASES).filter(([n]) => n === "hmac-valid");
await handler(new Request("http://app.test/api/lago/webhooks", { method: "POST", body: hb, headers: { ...hh, "x-lago-unique-key": "key-hmac-valid" } }));
console.log(JSON.stringify({ first, replay, contractError, usageCents: usage.amount_cents, entitled, balance, routeStatuses, inserted }));
"""


if __name__ == "__main__":
    unittest.main()
