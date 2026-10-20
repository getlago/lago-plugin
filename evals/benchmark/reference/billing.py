"""Reference solution for the python-usage-billing benchmark task.

It exists to prove the scorer: tests/test_benchmark.py requires it to pass every
criterion and requires targeted mutations of it to fail. It is not shown to agents.
"""

import base64
import hashlib
import hmac
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

from app import db

METRIC_CODE = "llm_tokens"
PLAN_CODE = "pro"


class LagoError(Exception):
    def __init__(self, status, body):
        super().__init__(f"Lago API error {status}")
        self.status, self.body = status, body


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "redirect refused", headers, fp)


_opener = urllib.request.build_opener(_NoRedirect())


def _lago(method, path, body=None):
    request = urllib.request.Request(
        os.environ["LAGO_API_URL"].rstrip("/") + "/api/v1" + path,
        data=None if body is None else json.dumps(body).encode(),
        method=method,
        headers={"Authorization": "Bearer " + os.environ["LAGO_API_KEY"], "Content-Type": "application/json"},
    )
    try:
        with _opener.open(request, timeout=10) as response:
            text = response.read()
            return json.loads(text) if text else None
    except urllib.error.HTTPError as error:
        with error:
            text = error.read()
        try:
            payload = json.loads(text) if text else None
        except ValueError:
            payload = None
        raise LagoError(error.code, payload) from None


def _schema():
    with db.connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS usage_outbox (
              generation_id TEXT PRIMARY KEY, transaction_id TEXT NOT NULL, subscription_id TEXT NOT NULL,
              occurred_at REAL NOT NULL, tokens INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending'
            );
            CREATE TABLE IF NOT EXISTS webhook_inbox (unique_key TEXT PRIMARY KEY, payload TEXT NOT NULL);
            """
        )


def setup_catalog():
    try:
        metric = _lago("GET", f"/billable_metrics/{METRIC_CODE}")["billable_metric"]
    except LagoError as error:
        if error.status != 404:
            raise
        metric = _lago("POST", "/billable_metrics", {"billable_metric": {
            "name": "LLM tokens", "code": METRIC_CODE, "aggregation_type": "sum_agg", "field_name": "tokens", "recurring": False}})["billable_metric"]
    try:
        _lago("GET", f"/plans/{PLAN_CODE}")
    except LagoError as error:
        if error.status != 404:
            raise
        _lago("POST", "/plans", {"plan": {
            "name": "Pro", "code": PLAN_CODE, "interval": "monthly", "amount_cents": 4900, "amount_currency": "USD",
            "pay_in_advance": True,
            "charges": [{"billable_metric_id": metric["lago_id"], "charge_model": "standard", "pay_in_advance": False,
                         "properties": {"amount": "0.00002"}}]}})


def _subscription_id(workspace_id):
    return f"sub_{workspace_id}"


def activate_billing(workspace_id):
    with db.connect() as conn:
        workspace = dict(conn.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,)).fetchone())
    _lago("POST", "/customers", {"customer": {"external_id": workspace_id, "name": workspace["name"],
                                               "email": workspace["email"], "currency": "USD"}})
    _lago("POST", "/subscriptions", {"subscription": {
        "external_id": _subscription_id(workspace_id), "external_customer_id": workspace_id, "plan_code": PLAN_CODE,
        "billing_time": "anniversary", "subscription_at": datetime.now(timezone.utc).isoformat()}})


def record_usage(generation_id):
    _schema()
    generation = db.get_generation(generation_id)
    occurred_at = datetime.fromisoformat(generation["created_at"]).timestamp()
    with db.connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO usage_outbox (generation_id, transaction_id, subscription_id, occurred_at, tokens) VALUES (?, ?, ?, ?, ?)",
            (generation_id, f"gen_{generation_id}", _subscription_id(generation["workspace_id"]), occurred_at,
             generation["input_tokens"] + generation["output_tokens"]),
        )
    flush_usage()


def flush_usage():
    _schema()
    with db.connect() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM usage_outbox WHERE status = 'pending'")]
    for row in rows:
        event = {"transaction_id": row["transaction_id"], "external_subscription_id": row["subscription_id"],
                 "code": METRIC_CODE, "timestamp": f"{row['occurred_at']:.3f}", "properties": {"tokens": row["tokens"]}}
        try:
            _lago("POST", "/events", {"event": event})
            status = "delivered"
        except LagoError as error:
            details = (error.body or {}).get("error_details") or {}
            if error.status == 422 and "value_already_exist" in details.get("transaction_id", []):
                status = "duplicate_to_reconcile"  # never resend under a new ID
            elif error.status == 429 or error.status >= 500:
                continue  # retried on the next flush with the same ID and timestamp
            else:
                status = "rejected"
        except (urllib.error.URLError, TimeoutError):
            continue
        with db.connect() as conn:
            conn.execute("UPDATE usage_outbox SET status = ? WHERE generation_id = ?", (status, row["generation_id"]))


def handle_lago_webhook(raw_body, headers):
    if headers.get("X-Lago-Signature-Algorithm") != "hmac":
        return 401
    expected = base64.b64encode(hmac.new(os.environ["LAGO_WEBHOOK_HMAC_KEY"].encode(), raw_body, hashlib.sha256).digest()).decode()
    if not hmac.compare_digest(expected, headers.get("X-Lago-Signature") or ""):
        return 401
    unique_key = headers.get("X-Lago-Unique-Key")
    if not unique_key:
        return 400
    _schema()
    with db.connect() as conn:
        conn.execute("INSERT OR IGNORE INTO webhook_inbox (unique_key, payload) VALUES (?, ?)", (unique_key, raw_body.decode()))
    return 204
