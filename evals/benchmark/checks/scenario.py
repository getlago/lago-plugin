"""Drive a finished workspace's billing.py through the benchmark scenario.

Runs inside the workspace (cwd), in a child process started by score.py. It only
calls the public contract from the task prompt and writes what happened to the
JSON path given as the first argument. Correctness is judged by score.py from
what the fake Lago received, not from anything this script prints.
"""

import base64
import hashlib
import hmac
import importlib
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone


class Headers(dict):
    """Case-insensitive lookups, like every web framework's header mapping."""

    def __init__(self, values):
        super().__init__(values)
        self._lower = {k.lower(): v for k, v in values.items()}

    def __getitem__(self, key):
        return self._lower[key.lower()]

    def get(self, key, default=None):
        return self._lower.get(key.lower(), default)

    def __contains__(self, key):
        return isinstance(key, str) and key.lower() in self._lower


def main(result_path):
    sys.path.insert(0, os.getcwd())
    results = {"steps": {}, "webhooks": {}, "generations": {}}

    def step(name, call):
        started = time.monotonic()
        try:
            value = call()
            results["steps"][name] = {"ok": True, "seconds": round(time.monotonic() - started, 2), "value": repr(value)[:200]}
        except BaseException as error:  # noqa: BLE001 - record any failure of the code under test
            results["steps"][name] = {"ok": False, "error": "".join(traceback.format_exception_only(type(error), error)).strip()[:500]}
        with open(result_path, "w", encoding="utf-8") as handle:
            json.dump(results, handle)

    try:
        db = importlib.import_module("app.db")
        db.init_db()
        db.create_workspace("ws_acme", "Acme", "billing@acme.test")
    except BaseException as error:  # noqa: BLE001 - the agent changed app/db.py incompatibly
        results["import_error"] = "app/db.py contract broken: " + "".join(traceback.format_exception_only(type(error), error)).strip()[:400]
        with open(result_path, "w", encoding="utf-8") as handle:
            json.dump(results, handle)
        return
    try:
        billing = importlib.import_module("billing")
    except BaseException as error:  # noqa: BLE001
        results["import_error"] = "".join(traceback.format_exception_only(type(error), error)).strip()[:500]
        with open(result_path, "w", encoding="utf-8") as handle:
            json.dump(results, handle)
        return

    step("setup_catalog", billing.setup_catalog)
    step("activate_billing", lambda: billing.activate_billing("ws_acme"))
    time.sleep(1.1)  # usage happens after activation, as in production
    for name, tokens in (("g1", (80000, 20000)), ("g2", (15000, 5000))):
        generation_id = db.create_generation("ws_acme", "acme-small", *tokens)
        results["generations"][name] = {"id": generation_id, "created_at": db.get_generation(generation_id)["created_at"]}
    step("record_usage_g1", lambda: billing.record_usage(results["generations"]["g1"]["id"]))
    step("record_usage_g2", lambda: billing.record_usage(results["generations"]["g2"]["id"]))
    step("flush_1", billing.flush_usage)
    step("flush_2", billing.flush_usage)
    step("replay_g1", lambda: billing.record_usage(results["generations"]["g1"]["id"]))
    step("flush_3", billing.flush_usage)
    time.sleep(1)  # allow background delivery threads to finish

    key = os.environ["LAGO_WEBHOOK_HMAC_KEY"].encode()
    body = json.dumps({"webhook_type": "invoice.created", "object_type": "invoice", "invoice": {"lago_id": "inv_bench_1"}}).encode()

    def sign(data, secret=key):
        return base64.b64encode(hmac.new(secret, data, hashlib.sha256).digest()).decode()

    cases = {
        "valid": (body, {"X-Lago-Signature": sign(body), "X-Lago-Signature-Algorithm": "hmac", "X-Lago-Unique-Key": "wh_1"}),
        "replay": (body, {"X-Lago-Signature": sign(body), "X-Lago-Signature-Algorithm": "hmac", "X-Lago-Unique-Key": "wh_1"}),
        "tampered_body": (body.replace(b"inv_bench_1", b"inv_bench_2"),
                          {"X-Lago-Signature": sign(body), "X-Lago-Signature-Algorithm": "hmac", "X-Lago-Unique-Key": "wh_2"}),
        "wrong_key": (body, {"X-Lago-Signature": sign(body, b"not-the-key"), "X-Lago-Signature-Algorithm": "hmac", "X-Lago-Unique-Key": "wh_3"}),
        "unsigned": (body, {"X-Lago-Unique-Key": "wh_4"}),
    }
    for name, (raw, headers) in cases.items():
        try:
            status = billing.handle_lago_webhook(raw, Headers(headers))
            results["webhooks"][name] = {"status": status if isinstance(status, int) else repr(status)}
        except BaseException as error:  # noqa: BLE001
            results["webhooks"][name] = {"error": "".join(traceback.format_exception_only(type(error), error)).strip()[:300]}
    results["finished_at"] = datetime.now(timezone.utc).isoformat()
    with open(result_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle)


if __name__ == "__main__":
    main(sys.argv[1])
