"""A local fake of the Lago REST endpoints the benchmark task needs; standard library only.

Required request fields follow https://swagger.getlago.com/openapi.yaml (checked
2026-10-19): billable metrics need `name`, `code`, `aggregation_type`; plans need
`name`, `code`, `interval`, `amount_cents`, `amount_currency`, `pay_in_advance`, and
each charge `billable_metric_id` and `charge_model`; customers need `external_id`;
subscriptions need `external_customer_id`, `plan_code`, `external_id`; events need
`transaction_id`, `external_subscription_id`, `code`. Duplicate `transaction_id`
values return 422 `value_already_exist`, the documented Postgres event-store
behavior. Every request is recorded so checks can inspect retries and payloads.
"""

from __future__ import annotations

import json
import threading
import uuid
from decimal import Decimal, InvalidOperation
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

API_KEY = "benchmark-key-not-a-secret"


def unprocessable(details: dict) -> tuple[int, dict]:
    return 422, {"status": 422, "error": "Unprocessable Entity", "code": "validation_errors", "error_details": details}


def missing(payload: dict, fields: tuple[str, ...]) -> dict:
    return {field: ["value_is_mandatory"] for field in fields if payload.get(field) in (None, "")}


def decimal(value) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def charge_amount(model: str, properties: dict, units: Decimal) -> Decimal | None:
    """Amount in currency units for `units`, for the charge models a usage price can use."""
    properties = properties or {}
    if model == "standard":
        amount = decimal(properties.get("amount"))
        return None if amount is None else amount * units
    if model == "package":
        amount, size = decimal(properties.get("amount")), decimal(properties.get("package_size"))
        free = decimal(properties.get("free_units", 0)) or Decimal(0)
        if amount is None or not size:
            return None
        billable = max(units - free, Decimal(0))
        packages = -(-billable // size)  # whole packages, rounded up
        return amount * packages
    if model in ("graduated", "volume"):
        ranges = properties.get(f"{model}_ranges") or []
        total = Decimal(0)
        for tier in ranges:
            low = Decimal(tier["from_value"])
            high = None if tier.get("to_value") is None else Decimal(tier["to_value"])
            per_unit, flat = decimal(tier.get("per_unit_amount", "0")), decimal(tier.get("flat_amount", "0"))
            if per_unit is None or flat is None:
                return None
            if model == "volume":
                if units >= low and (high is None or units <= high):
                    return per_unit * units + flat
                continue
            floor = low - 1 if low > 0 else Decimal(0)  # tiers are inclusive: 0-10, 11-20, ...
            if units > floor:
                in_tier = (units if high is None else min(units, high)) - floor
                total += per_unit * in_tier + flat
        return total if model == "graduated" else None
    return None


class FakeLago:
    def __init__(self, fail_first_event_posts: int = 1):
        self.lock = threading.Lock()
        self.requests: list[dict] = []
        self.metrics: dict[str, dict] = {}
        self.plans: dict[str, dict] = {}
        self.customers: dict[str, dict] = {}
        self.subscriptions: dict[str, dict] = {}
        self.events: dict[str, dict] = {}
        self.fail_event_posts = fail_first_event_posts
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    # Routing -----------------------------------------------------------------

    def handle(self, method: str, path: str, body) -> tuple[int, object]:
        url = urlparse(path)
        parts = [p for p in url.path.split("/") if p]
        if parts == ["__bench", "state"]:
            # Scenario-only progress probe, used to stop polling early. Not part of the Lago API.
            attempted = {e.get("transaction_id") for r in self.requests if r["method"] == "POST" and "/events" in r["path"]
                         for e in ((r["body"] or {}).get("events") or [(r["body"] or {}).get("event") or {}])}
            return 200, {"stored": len(self.events), "unstored_attempts": len([t for t in attempted if t not in self.events])}
        if parts[:2] != ["api", "v1"]:
            return 404, {"status": 404, "error": "Not Found"}
        route, rest = parts[2] if len(parts) > 2 else "", parts[3:]
        if method == "POST" and route == "billable_metrics" and not rest:
            return self.create_metric((body or {}).get("billable_metric") or {})
        if method == "GET" and route == "billable_metrics" and len(rest) == 1:
            metric = self.metrics.get(rest[0])
            return (200, {"billable_metric": metric}) if metric else (404, {"status": 404, "error": "Not Found", "code": "billable_metric_not_found"})
        if method == "POST" and route == "plans" and not rest:
            return self.create_plan((body or {}).get("plan") or {})
        if method == "GET" and route == "plans" and len(rest) == 1:
            plan = self.plans.get(rest[0])
            return (200, {"plan": plan}) if plan else (404, {"status": 404, "error": "Not Found", "code": "plan_not_found"})
        if method == "POST" and route == "customers" and not rest:
            return self.upsert_customer((body or {}).get("customer") or {})
        if method == "POST" and route == "subscriptions" and not rest:
            return self.create_subscription((body or {}).get("subscription") or {})
        if method == "POST" and route == "events" and not rest:
            return self.create_events([(body or {}).get("event") or {}], batch=False)
        if method == "POST" and route == "events" and rest == ["batch"]:
            return self.create_events((body or {}).get("events") or [], batch=True)
        if method == "GET" and route == "customers" and len(rest) == 2 and rest[1] == "current_usage":
            query = parse_qs(url.query)
            return self.current_usage(rest[0], (query.get("external_subscription_id") or [""])[0])
        return 404, {"status": 404, "error": "Not Found"}

    def create_metric(self, payload: dict) -> tuple[int, object]:
        errors = missing(payload, ("name", "code", "aggregation_type"))
        if errors:
            return unprocessable(errors)
        if payload["code"] in self.metrics:
            return unprocessable({"code": ["value_already_exist"]})
        metric = {**payload, "lago_id": str(uuid.uuid4())}
        self.metrics[payload["code"]] = metric
        return 200, {"billable_metric": metric}

    def create_plan(self, payload: dict) -> tuple[int, object]:
        errors = missing(payload, ("name", "code", "interval", "amount_cents", "amount_currency", "pay_in_advance"))
        ids = {m["lago_id"] for m in self.metrics.values()}
        for index, charge in enumerate(payload.get("charges") or []):
            if not charge.get("charge_model"):
                errors[f"charges[{index}].charge_model"] = ["value_is_mandatory"]
            if charge.get("billable_metric_id") not in ids:
                errors[f"charges[{index}].billable_metric_id"] = ["billable_metric_not_found"]
        if errors:
            return unprocessable(errors)
        if payload["code"] in self.plans:
            return unprocessable({"code": ["value_already_exist"]})
        self.plans[payload["code"]] = {**payload, "lago_id": str(uuid.uuid4())}
        return 200, {"plan": self.plans[payload["code"]]}

    def upsert_customer(self, payload: dict) -> tuple[int, object]:
        errors = missing(payload, ("external_id",))
        if errors:
            return unprocessable(errors)
        customer = {**self.customers.get(payload["external_id"], {}), **payload}
        self.customers[payload["external_id"]] = customer
        return 200, {"customer": customer}

    def create_subscription(self, payload: dict) -> tuple[int, object]:
        errors = missing(payload, ("external_customer_id", "plan_code", "external_id"))
        if errors:
            return unprocessable(errors)
        if payload["external_customer_id"] not in self.customers:
            return 404, {"status": 404, "error": "Not Found", "code": "customer_not_found"}
        if payload["plan_code"] not in self.plans:
            return 404, {"status": 404, "error": "Not Found", "code": "plan_not_found"}
        self.subscriptions[payload["external_id"]] = {**payload, "status": "active"}
        return 200, {"subscription": self.subscriptions[payload["external_id"]]}

    def create_events(self, events: list, batch: bool) -> tuple[int, object]:
        if self.fail_event_posts > 0:
            self.fail_event_posts -= 1
            return 503, {"status": 503, "error": "Service Unavailable"}
        for event in events:
            errors = missing(event, ("transaction_id", "external_subscription_id", "code"))
            if errors:
                return unprocessable(errors)
            if event["transaction_id"] in self.events:
                return unprocessable({"transaction_id": ["value_already_exist"]})
        for event in events:
            self.events[event["transaction_id"]] = event
        return 200, ({"events": events} if batch else {"event": events[0]})

    # Observations ------------------------------------------------------------

    def usage_units(self, subscription_id: str, metric: dict) -> Decimal | None:
        field = metric.get("field_name")
        total = Decimal(0)
        for event in self.events.values():
            if event.get("external_subscription_id") != subscription_id or event.get("code") != metric["code"]:
                continue
            if metric.get("aggregation_type") == "count_agg":
                total += 1
                continue
            value = decimal((event.get("properties") or {}).get(field))
            if value is None:
                return None
            total += value
        return total

    def current_usage(self, customer_id: str, subscription_id: str) -> tuple[int, object]:
        subscription = self.subscriptions.get(subscription_id)
        if not subscription or subscription["external_customer_id"] != customer_id:
            return 404, {"status": 404, "error": "Not Found", "code": "subscription_not_found"}
        plan = self.plans[subscription["plan_code"]]
        cents = Decimal(0)
        for charge in plan.get("charges") or []:
            metric = next(m for m in self.metrics.values() if m["lago_id"] == charge["billable_metric_id"])
            units = self.usage_units(subscription_id, metric)
            amount = None if units is None else charge_amount(charge["charge_model"], charge.get("properties"), units)
            if amount is not None:
                cents += amount * 100
        return 200, {"customer_usage": {"amount_cents": int(cents.to_integral_value()), "currency": plan["amount_currency"]}}

    def _handler(self):
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _serve(self, method: str):
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b""
                try:
                    body = json.loads(raw) if raw else None
                except ValueError:
                    body = None
                with fake.lock:
                    if not self.path.startswith("/__bench/"):
                        fake.requests.append({"method": method, "path": self.path, "body": body})
                    if self.path.startswith("/__bench/"):
                        status, payload = fake.handle(method, self.path, body)
                    elif self.headers.get("Authorization") != f"Bearer {API_KEY}":
                        status, payload = 401, {"status": 401, "error": "Unauthorized"}
                    else:
                        status, payload = fake.handle(method, self.path, body)
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                self._serve("GET")

            def do_POST(self):
                self._serve("POST")

            def do_PUT(self):
                self._serve("PUT")

        return Handler
