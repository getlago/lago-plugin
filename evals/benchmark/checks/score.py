#!/usr/bin/env python3
"""Score one finished workspace on the benchmark's four billing-correctness criteria.

The workspace is copied to a temporary directory and its billing.py runs in a child
process against a local fake Lago (fake_lago.py), with a clean environment that holds
only fake credentials. The first event delivery fails with HTTP 503 so retries are
observable. Criteria are judged from what the fake received:

After the scripted calls, the scenario keeps calling flush_usage() once a second
for up to 90 seconds, like a worker, so solutions that back off before retrying
are not penalized.

- idempotent_events: every event attempt has an explicit timestamp; attempts with
  the same transaction_id share it; every attempted transaction_id is eventually
  stored, so the failed delivery was retried with its original ID, not dropped or
  re-minted.
- no_double_billing: after replaying one generation, stored usage on the
  subscription is exactly 120,000 tokens, and the subscription's external_id
  differs from the customer's external_id.
- correct_charges: the configured plan is $49.00 USD monthly and its usage charge
  prices 120,000 tokens at $2.40; at least one stored event targets that metric
  with its aggregation field present.
- webhook_verification: a valid HMAC webhook and its replay return 2xx; a tampered
  body, a wrong key, and a missing signature return 4xx.

Each criterion is "pass" or "fail" with reasons. If the scorer itself cannot run the
scenario, the result is "error" and the run is incomplete, never a pass.

Usage: score.py <workspace> [--timeout SECONDS]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path

CHECKS = Path(__file__).resolve().parent
sys.path.insert(0, str(CHECKS))
from fake_lago import API_KEY, FakeLago, charge_amount  # noqa: E402

HMAC_KEY = "benchmark-hmac-key"
TOTAL_TOKENS = Decimal(120000)
CRITERIA = ("idempotent_events", "no_double_billing", "correct_charges", "webhook_verification")


def event_attempts(fake: FakeLago) -> list[dict]:
    attempts = []
    for request in fake.requests:
        if request["method"] != "POST" or not request["path"].split("?")[0].rstrip("/").endswith(("/events", "/events/batch")):
            continue
        body = request["body"] or {}
        attempts.extend(body.get("events") or ([body["event"]] if isinstance(body.get("event"), dict) else []))
    return attempts


def usage_charge(fake: FakeLago):
    """The plan, metric, and charge that price usage, if exactly one plan exists."""
    if len(fake.plans) != 1:
        return None, None, None, f"expected one plan, found {len(fake.plans)}"
    plan = next(iter(fake.plans.values()))
    charges = plan.get("charges") or []
    if len(charges) != 1:
        return plan, None, None, f"expected one usage charge, found {len(charges)}"
    charge = charges[0]
    metric = next((m for m in fake.metrics.values() if m["lago_id"] == charge["billable_metric_id"]), None)
    return plan, metric, charge, None


def judge(fake: FakeLago, scenario: dict) -> dict:
    out = {name: {"result": "fail", "reasons": []} for name in CRITERIA}
    if scenario.get("import_error"):
        for name in CRITERIA:
            out[name]["reasons"].append(f"billing.py failed to import: {scenario['import_error']}")
        return out
    plan, metric, charge, problem = usage_charge(fake)
    subscription = next(iter(fake.subscriptions.values()), None) if len(fake.subscriptions) == 1 else None

    # idempotent_events
    reasons = out["idempotent_events"]["reasons"]
    attempts = event_attempts(fake)
    by_id: dict[str, set] = {}
    for event in attempts:
        by_id.setdefault(event.get("transaction_id"), set()).add(json.dumps(event.get("timestamp")))
    if not attempts:
        reasons.append("no usage event was sent")
    if any(e.get("timestamp") in (None, "") for e in attempts):
        reasons.append("an event was sent without an explicit timestamp")
    if any(len(stamps) > 1 for stamps in by_id.values()):
        reasons.append("a retry changed the timestamp of an existing transaction_id")
    orphans = [tid for tid in by_id if tid not in fake.events]
    if orphans:
        reasons.append(f"{len(orphans)} attempted transaction_id(s) never stored: the failed delivery was dropped or retried under a new ID")
    if not reasons:
        out["idempotent_events"]["result"] = "pass"

    # no_double_billing
    reasons = out["no_double_billing"]["reasons"]
    if subscription is None:
        reasons.append(f"expected one subscription, found {len(fake.subscriptions)}")
    elif metric is None:
        reasons.append(problem or "usage charge has no metric")
    else:
        units = fake.usage_units(subscription["external_id"], metric)
        if units != TOTAL_TOKENS:
            reasons.append(f"stored usage is {units} tokens after a replay, expected {TOTAL_TOKENS}")
        if subscription["external_id"] == subscription["external_customer_id"]:
            reasons.append("subscription external_id reuses the customer external_id")
    if not scenario.get("steps", {}).get("replay_g1", {}).get("ok"):
        reasons.append("record_usage raised on a replayed generation")
    if not reasons:
        out["no_double_billing"]["result"] = "pass"

    # correct_charges
    reasons = out["correct_charges"]["reasons"]
    if problem or metric is None:
        reasons.append(problem or "usage charge has no metric")
    else:
        if (plan.get("amount_cents"), str(plan.get("amount_currency")).upper(), plan.get("interval")) != (4900, "USD", "monthly"):
            reasons.append(f"plan is {plan.get('amount_cents')} {plan.get('amount_currency')} {plan.get('interval')}, expected 4900 USD monthly")
        amount = charge_amount(charge.get("charge_model"), charge.get("properties"), TOTAL_TOKENS)
        if amount is None or amount != Decimal("2.40"):
            reasons.append(f"usage charge prices {TOTAL_TOKENS} tokens at {amount}, expected 2.40")
        if metric.get("aggregation_type") not in ("sum_agg",):
            reasons.append(f"metric aggregation is {metric.get('aggregation_type')}, expected sum_agg over tokens")
        field = metric.get("field_name")
        matching = [e for e in fake.events.values() if e.get("code") == metric["code"]]
        if not matching:
            reasons.append("no stored event uses the plan's metric code")
        elif not all(field in (e.get("properties") or {}) for e in matching):
            reasons.append(f"stored events lack the metric field `{field}`")
    if not reasons:
        out["correct_charges"]["result"] = "pass"

    # webhook_verification
    reasons = out["webhook_verification"]["reasons"]
    webhooks = scenario.get("webhooks", {})
    expected = {"valid": "2xx", "replay": "2xx", "tampered_body": "4xx", "wrong_key": "4xx", "unsigned": "4xx"}
    for name, want in expected.items():
        status = webhooks.get(name, {}).get("status")
        ok = isinstance(status, int) and (200 <= status < 300 if want == "2xx" else 400 <= status < 500)
        if not ok:
            reasons.append(f"{name}: expected {want}, got {webhooks.get(name)}")
    if not reasons:
        out["webhook_verification"]["result"] = "pass"
    return out


def score(workspace: Path, timeout: int = 240, flush_window: int = 90) -> dict:
    fake = FakeLago(fail_first_event_posts=1)
    try:
        with tempfile.TemporaryDirectory(prefix="lago-bench-") as temp:
            root = Path(temp)
            work = root / "workspace"
            shutil.copytree(workspace, work, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.db"))
            result_path = root / "scenario.json"
            env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": str(root),
                "LAGO_API_URL": fake.url,
                "LAGO_API_KEY": API_KEY,
                "LAGO_WEBHOOK_HMAC_KEY": HMAC_KEY,
                "ACME_DB_PATH": str(root / "acme.db"),
                "PYTHONDONTWRITEBYTECODE": "1",
                "BENCH_FLUSH_WINDOW": str(flush_window),
            }
            started = datetime.now()
            try:
                completed = subprocess.run([sys.executable, str(CHECKS / "scenario.py"), str(result_path)], cwd=work, env=env,
                                           capture_output=True, text=True, timeout=timeout)
                exit_code, timed_out = completed.returncode, False
            except subprocess.TimeoutExpired:
                exit_code, timed_out = None, True
            seconds = round((datetime.now() - started).total_seconds(), 1)
            if not result_path.is_file():
                return {"status": "error", "reason": "scenario produced no result", "exit_code": exit_code, "timed_out": timed_out}
            scenario = json.loads(result_path.read_text(encoding="utf-8"))
        criteria = judge(fake, scenario)
        if timed_out:
            for value in criteria.values():
                value["reasons"].append(f"scenario timed out after {timeout}s")
                value["result"] = "fail"
        return {"status": "scored", "seconds": seconds, "timed_out": timed_out, "exit_code": exit_code,
                "criteria": criteria, "steps": scenario.get("steps", {}), "webhooks": scenario.get("webhooks", {}),
                "requests": len(fake.requests)}
    finally:
        fake.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()
    result = score(args.workspace.resolve(), args.timeout)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "scored" else 2


if __name__ == "__main__":
    sys.exit(main())
