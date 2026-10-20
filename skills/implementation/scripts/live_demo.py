#!/usr/bin/env python3
"""Turn the offline Atlas AI demo into real, finalized Lago invoices on a fresh local instance.

Optional, never the default: the offline walkthrough (`run_demo.py`) needs nothing.
This script only targets a self-hosted Lago it creates itself, in a dedicated
Docker Compose project bound to loopback ports. It never accepts a Lago Cloud,
remote, or pre-existing target. Standard library only, plus the Docker CLI.

Every phase that changes something requires an explicit approval flag that names
that phase. An agent passes it only after the user approved the exact gate that
`plan` and the phase itself print. Approval of one phase never covers another.

  plan                              Show the gates; changes nothing.
  up --approve infrastructure       Pull the pinned image, start a fresh project, bootstrap one org.
  verify                            Read-only: wait for the instance, re-trace it, re-check isolation.
  seed --approve seed               Create the Atlas catalog, customer, subscription, wallet, usage; replay.
  finalize --approve finalize       Terminate the subscription, collect finalized invoices, run money tests.
  teardown --approve teardown       Remove exactly this project's container and volume.

State (the generated API key and password included) lives in a private directory
outside any repository, mode 0700, and is never printed. Evidence is written there
too: sanitized Lago payloads, expected and actual money tests, and run metadata.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import secrets
import socket
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
# Pinned release: tag and multi-platform index digest, checked 2026-10-20.
IMAGE = "getlago/lago:v1.55.0@sha256:60ecc02cdb2854c918e28a6436ccb4033d8f4a0447bc0b5150936596ebe2a290"
PROJECT_PREFIX = "lago-plugin-demo-"
STATE_ROOT = Path(os.environ.get("LAGO_PLUGIN_DEMO_HOME", Path.home() / ".lago-plugin-demo"))

# The canonical Atlas AI example (examples/per-token-ai.md), prefixed for the demo.
PREFIX = "lago_plugin_demo_"
METRIC = PREFIX + "ai_tokens"
PLAN = PREFIX + "atlas_pro"
CUSTOMER = PREFIX + "acme"
SUBSCRIPTION = PREFIX + "acme_atlas_pro"
PRICES = {("demo-small", "input"): "0.00001", ("demo-small", "output"): "0.00003",
          ("demo-large", "input"): "0.00002", ("demo-large", "output"): "0.00006"}
PRIOR_USAGE = ("demo_prior_usage", "demo-small", "input", 980000)  # $9.80 already used this month
JOB = [("demo_evt_small_input", "demo-small", "input", 12000), ("demo_evt_small_output", "demo-small", "output", 3000),
       ("demo_evt_large_input", "demo-large", "input", 5000), ("demo_evt_large_output", "demo-large", "output", 1000)]
PLAN_FEE_CENTS, WALLET_GRANT = 9900, "10"


# Expected money, calculated independently of Lago ------------------------------------

def money(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def effective_price(subtotal: Decimal, quantity: Decimal) -> str:
    with localcontext() as context:
        context.prec = 28
        rendered = format(subtotal / quantity, "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


def expected() -> dict:
    events = [PRIOR_USAGE, *JOB]
    units = sum(Decimal(e[3]) for e in events)
    usage = sum(Decimal(e[3]) * Decimal(PRICES[(e[1], e[2])]) for e in events)
    credit = min(Decimal(WALLET_GRANT), usage)
    subscription = Decimal(PLAN_FEE_CENTS) / 100
    return {
        "subscription_invoice": {"currency": "USD", "quantity": "1", "unit_price": money(subscription),
                                 "subtotal": money(subscription), "discounts": "0.00", "credits": "0.00",
                                 "tax": "0.00", "total": money(subscription)},
        "usage_invoice": {"currency": "USD", "quantity": str(units), "unit_price": effective_price(usage, units),
                          "subtotal": money(usage), "discounts": "0.00", "credits": money(credit),
                          "tax": "0.00", "total": money(usage - credit)},
        "job_amount": money(sum(Decimal(e[3]) * Decimal(PRICES[(e[1], e[2])]) for e in JOB)),
        "period_total": money(subscription + usage - credit),
    }


# Gates -----------------------------------------------------------------------------

GATES = {
    "infrastructure": {
        "target": "this machine's Docker, a new Compose project named lago-plugin-demo-<suffix>",
        "action": f"pull {IMAGE}; create one container and one named volume; bind two free 127.0.0.1 ports",
        "objects": "one Lago organization with a generated API key and admin user (stored privately, mode 0600)",
        "billing_impact": "none: a disposable local instance with no payment, tax, email, or webhook destination",
        "infrastructure_impact": "image download (about 1 GB), one running container until teardown",
        "recovery": "teardown --approve teardown removes exactly this container and volume",
    },
    "seed": {
        "target": "the local instance created by `up`, re-validated as loopback and traced to its container",
        "action": "POST billable metric, plan, customer, subscription, wallet; POST 5 usage events; replay 1 event",
        "objects": f"{METRIC}, {PLAN}, {CUSTOMER}, {SUBSCRIPTION}, one granted $10 wallet restricted to {METRIC}",
        "billing_impact": "synthetic only: $99.00 in advance and $0.17 of overage on the local instance",
        "infrastructure_impact": "none beyond the running container",
        "recovery": "teardown deletes the instance and all its data",
    },
    "finalize": {
        "target": "the same local instance",
        "action": f"DELETE /subscriptions/{SUBSCRIPTION}?on_termination_credit_note=skip&on_termination_invoice=generate",
        "objects": "the demo subscription and its finalized invoices",
        "billing_impact": "closes the synthetic period; finalizes the usage invoice on the local instance",
        "infrastructure_impact": "none",
        "recovery": "teardown deletes the instance and all its data",
    },
    "teardown": {
        "target": "the Compose project recorded in this demo's state",
        "action": "docker compose down --volumes for that project only; delete its private state directory",
        "objects": "one container, one network, one volume",
        "billing_impact": "none",
        "infrastructure_impact": "frees the two loopback ports",
        "recovery": "none: the demo data is deleted",
    },
}


def show_gate(phase: str) -> None:
    print(f"\nGate: {phase}")
    for key, value in GATES[phase].items():
        print(f"  {key.replace('_', ' '):<22} {value}")


def require(phase: str, approved: str | None) -> None:
    show_gate(phase)
    if approved != phase:
        raise SystemExit(f"\nNot approved. Re-run with --approve {phase} only after the user approves this exact gate.")


# State and Docker ------------------------------------------------------------------

def private_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(stat.S_IRWXU)
    return path


def load_state(project: str) -> dict:
    path = STATE_ROOT / project / "state.json"
    if not path.is_file():
        raise SystemExit(f"No demo state for {project}. Run `up` first.")
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    directory = private_dir(STATE_ROOT / state["project"])
    path = directory / "state.json"
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def docker(*args: str, check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], capture_output=True, text=True, check=check, cwd=cwd)


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def compose_file(state: dict) -> str:
    env = {
        "LAGO_API_URL": state["api_url"], "LAGO_FRONT_URL": state["ui_url"], "API_URL": state["api_url"],
        "LAGO_CREATE_ORG": "true", "LAGO_ORG_NAME": "Lago plugin demo", "LAGO_ORG_USER_EMAIL": state["email"],
        "LAGO_ORG_USER_PASSWORD": state["password"], "LAGO_ORG_API_KEY": state["api_key"],
        "LAGO_DISABLE_SIGNUP": "true", "LAGO_DISABLE_PDF_GENERATION": "true",
    }
    lines = ["services:", "  lago:", f"    image: {IMAGE}", f"    container_name: {state['project']}",
             "    ports:", f"      - \"127.0.0.1:{state['api_port']}:3000\"", f"      - \"127.0.0.1:{state['ui_port']}:80\"",
             "    environment:"]
    lines += [f"      {key}: {json.dumps(value)}" for key, value in env.items()]
    lines += ["    volumes:", "      - data:/data", "volumes:", "  data: {}", ""]
    return "\n".join(lines)


def traced_port(state: dict) -> int | None:
    """Ask Docker which host port the project's container publishes for the API."""
    result = docker("compose", "-p", state["project"], "-f", state["compose_file"], "port", "lago", "3000", check=False)
    host, _, port = result.stdout.strip().rpartition(":")
    return int(port) if result.returncode == 0 and host == "127.0.0.1" and port.isdigit() else None


def validate_target(state: dict) -> None:
    check = subprocess.run([sys.executable, "-I", str(SCRIPTS / "validate_demo_target.py"), state["api_url"],
                            "--compose-project", state["project"]], capture_output=True, text=True)
    if check.returncode != 0:
        raise SystemExit(f"Demo target validation failed:\n{check.stdout}")
    if traced_port(state) != state["api_port"]:
        raise SystemExit("The API URL does not trace to this demo project's published container port. Stopping.")


# Lago API --------------------------------------------------------------------------

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "redirect refused", headers, fp)


OPENER = urllib.request.build_opener(NoRedirect())


def lago(state: dict, method: str, path: str, body: dict | None = None) -> tuple[int, dict | None]:
    request = urllib.request.Request(f"{state['api_url']}/api/v1{path}", method=method,
                                     data=None if body is None else json.dumps(body).encode(),
                                     headers={"Authorization": f"Bearer {state['api_key']}", "Content-Type": "application/json"})
    try:
        with OPENER.open(request, timeout=30) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        with error:
            raw = error.read()
        try:
            return error.code, json.loads(raw) if raw else None
        except ValueError:
            return error.code, None
    except (urllib.error.URLError, OSError, http.client.HTTPException):
        return 0, None  # not reachable yet; callers decide whether to wait or stop


def ok(state: dict, method: str, path: str, body: dict | None = None) -> dict:
    status, payload = lago(state, method, path, body)
    if not 200 <= status < 300:
        raise SystemExit(f"{method} {path} returned HTTP {status}: {json.dumps(payload)[:400]}")
    return payload or {}


def wait_for(description: str, probe, timeout: int = 300, interval: float = 3):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = probe()
        if value:
            return value
        time.sleep(interval)
    raise SystemExit(f"Timed out waiting for {description}.")


def source_provenance() -> dict:
    """Commit and dirty state of the plugin checkout, when it is a Git checkout."""
    root = SCRIPTS.parents[1].parent
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=True).stdout.strip())
        return {"source_commit": commit, "source_dirty": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"source_commit": None, "source_dirty": None}


# Phases ----------------------------------------------------------------------------

def phase_plan(_args) -> None:
    exp = expected()
    print("Live demo plan. Nothing has changed. Offline remains the default; this is optional.")
    print(f"  Image: {IMAGE}")
    print(f"  State and evidence: {STATE_ROOT}/<project> (private, outside any repository)")
    print(f"  Expected: job {exp['job_amount']}, subscription invoice {exp['subscription_invoice']['total']}, "
          f"usage invoice {exp['usage_invoice']['total']} after {exp['usage_invoice']['credits']} of wallet credit, "
          f"period total {exp['period_total']} USD before tax")
    for phase in GATES:
        show_gate(phase)


def phase_up(args) -> None:
    require("infrastructure", args.approve)
    project = PROJECT_PREFIX + (args.suffix or secrets.token_hex(3))
    if (STATE_ROOT / project).exists() or docker("ps", "-a", "--filter", f"name=^{project}$", "-q").stdout.strip() \
            or docker("volume", "ls", "--filter", f"name=^{project}_", "-q").stdout.strip():
        raise SystemExit(f"{project} already exists. The demo only uses a fresh project; pick another --suffix.")
    api_port, ui_port = free_port(), free_port()
    directory = private_dir(STATE_ROOT / project)
    state = {"project": project, "image": IMAGE, "api_port": api_port, "ui_port": ui_port,
             "api_url": f"http://127.0.0.1:{api_port}", "ui_url": f"http://127.0.0.1:{ui_port}",
             "email": f"demo-{secrets.token_hex(4)}@example.com", "password": secrets.token_urlsafe(18),
             "api_key": secrets.token_hex(24), "compose_file": str(directory / "compose.yaml"),
             "created_at": datetime.now(timezone.utc).isoformat(), "objects": {}}
    Path(state["compose_file"]).write_text(compose_file(state), encoding="utf-8")
    Path(state["compose_file"]).chmod(stat.S_IRUSR | stat.S_IWUSR)
    save_state(state)
    print(f"\nStarting {project} (API {state['api_url']}, UI {state['ui_url']}) ...")
    docker("compose", "-p", project, "-f", state["compose_file"], "up", "-d", "--quiet-pull")
    verify_instance(state)


def phase_verify(args) -> None:
    """Read-only: wait for an existing demo instance, re-trace it, and re-check isolation."""
    verify_instance(load_state(args.project))


def verify_instance(state: dict) -> None:
    project = state["project"]
    wait_for("the Lago API", lambda: lago(state, "GET", "/organizations")[0] == 200, timeout=600, interval=5)
    validate_target(state)
    organization = ok(state, "GET", "/organizations").get("organization", {})
    endpoints = ok(state, "GET", "/webhook_endpoints").get("webhook_endpoints", [])
    isolation = {"webhook_endpoints": len(endpoints), "organization_webhook_urls": organization.get("webhook_urls") or [],
                 "smtp_configured": False, "pdf_generation": False, "events_store": organization.get("events_store")}
    if isolation["webhook_endpoints"] or isolation["organization_webhook_urls"]:
        raise SystemExit("The new instance has webhook destinations. Refusing to seed; run teardown.")
    state["isolation"] = isolation
    save_state(state)
    print(f"Ready. Isolation verified: {json.dumps(isolation)}")
    print(f"Next: show the `seed` gate to the user, then run: seed --project {project} --approve seed")


def phase_seed(args) -> None:
    state = load_state(args.project)
    require("seed", args.approve)
    validate_target(state)
    metric = ok(state, "POST", "/billable_metrics", {"billable_metric": {
        "name": "Lago plugin demo AI tokens", "code": METRIC, "aggregation_type": "sum_agg", "field_name": "tokens",
        "recurring": False, "filters": [{"key": "model", "values": ["demo-small", "demo-large"]},
                                         {"key": "type", "values": ["input", "output"]}]}})["billable_metric"]
    ok(state, "POST", "/plans", {"plan": {
        "name": "Atlas Pro", "code": PLAN, "interval": "monthly", "amount_cents": PLAN_FEE_CENTS, "amount_currency": "USD",
        "pay_in_advance": True, "charges": [{
            "billable_metric_id": metric["lago_id"], "charge_model": "standard", "pay_in_advance": False,
            "properties": {"amount": "0"},
            "filters": [{"invoice_display_name": f"{model} {kind}", "properties": {"amount": price},
                         "values": {"model": [model], "type": [kind]}} for (model, kind), price in PRICES.items()]}]}})
    customer = ok(state, "POST", "/customers", {"customer": {
        "external_id": CUSTOMER, "name": "Acme Corp (demo)", "currency": "USD"}})["customer"]
    subscription = ok(state, "POST", "/subscriptions", {"subscription": {
        "external_id": SUBSCRIPTION, "external_customer_id": CUSTOMER, "plan_code": PLAN, "billing_time": "anniversary",
        "subscription_at": datetime.now(timezone.utc).isoformat()}})["subscription"]
    wallet = ok(state, "POST", "/wallets", {"wallet": {
        "external_customer_id": CUSTOMER, "name": "Included AI usage (demo)", "currency": "USD", "rate_amount": "1",
        "granted_credits": WALLET_GRANT, "applies_to": {"billable_metric_codes": [METRIC]}}})["wallet"]
    wait_for("the granted wallet credit", lambda: Decimal(str(ok(state, "GET", f"/wallets/{wallet['lago_id']}")["wallet"]
                                                               .get("credits_balance") or 0)) == Decimal(WALLET_GRANT))
    started = datetime.fromisoformat(subscription["started_at"].replace("Z", "+00:00")).timestamp()
    time.sleep(max(0.0, started + 2 - time.time()))  # usage happens after activation, never before it
    stamp = time.time()
    sent = []
    for offset, (transaction, model, kind, tokens) in enumerate([PRIOR_USAGE, *JOB]):
        event = {"transaction_id": PREFIX + transaction, "external_subscription_id": SUBSCRIPTION, "code": METRIC,
                 "timestamp": f"{stamp + offset * 0.001:.3f}", "properties": {"tokens": tokens, "model": model, "type": kind}}
        ok(state, "POST", "/events", {"event": event})
        sent.append(event)
    query = f"/customers/{CUSTOMER}/current_usage?external_subscription_id={SUBSCRIPTION}"
    expected_cents = int((Decimal(expected()["usage_invoice"]["subtotal"]) * 100).to_integral_value())
    before = wait_for("usage to be rated", lambda: (lambda u: u if u["amount_cents"] == expected_cents else None)(
        ok(state, "GET", query)["customer_usage"]), timeout=180)
    replay_status, replay_body = lago(state, "POST", "/events", {"event": sent[1]})
    time.sleep(5)
    after = ok(state, "GET", query)["customer_usage"]
    replay = {"transaction_id": sent[1]["transaction_id"], "http_status": replay_status, "response": replay_body,
              "amount_cents_before": before["amount_cents"], "amount_cents_after": after["amount_cents"],
              "units_before": [c["units"] for c in before["charges_usage"]],
              "units_after": [c["units"] for c in after["charges_usage"]]}
    replay["no_double_billing"] = (replay["amount_cents_before"] == replay["amount_cents_after"]
                                   and replay["units_before"] == replay["units_after"])
    evidence = private_dir(STATE_ROOT / state["project"] / "evidence")
    (evidence / "lago-current-usage.json").write_text(json.dumps({"customer_usage": after}, indent=2) + "\n", encoding="utf-8")
    (evidence / "replay.json").write_text(json.dumps(replay, indent=2) + "\n", encoding="utf-8")
    state["objects"] = {"billable_metric": METRIC, "plan": PLAN, "customer": CUSTOMER, "customer_lago_id": customer["lago_id"],
                        "subscription": SUBSCRIPTION, "wallet_lago_id": wallet["lago_id"],
                        "events": [e["transaction_id"] for e in sent]}
    save_state(state)
    print(f"\nSeeded. Usage before invoicing: {before['amount_cents']} cents. Replay HTTP {replay_status}; "
          f"usage unchanged: {replay['no_double_billing']}.")
    if not replay["no_double_billing"]:
        raise SystemExit("The replay changed usage. Live proof incomplete.")
    print(f"Next: show the `finalize` gate to the user, then run: finalize --project {state['project']} --approve finalize")


def phase_finalize(args) -> None:
    state = load_state(args.project)
    require("finalize", args.approve)
    validate_target(state)
    status, _ = lago(state, "DELETE", f"/subscriptions/{SUBSCRIPTION}?on_termination_credit_note=skip&on_termination_invoice=generate")
    if not 200 <= status < 300:
        # Re-running finalize after termination only re-collects and re-tests the invoices.
        current = ok(state, "GET", f"/subscriptions/{SUBSCRIPTION}?status=terminated").get("subscription", {})
        if current.get("status") != "terminated":
            raise SystemExit(f"Termination returned HTTP {status} and the subscription is not terminated.")

    def finalized():
        listed = ok(state, "GET", f"/invoices?external_customer_id={CUSTOMER}&per_page=20")["invoices"]
        done = [i for i in listed if i.get("status") == "finalized"]
        return done if len(done) >= 2 else None

    invoices = [ok(state, "GET", f"/invoices/{i['lago_id']}") for i in wait_for("two finalized invoices", finalized, timeout=300)]
    evidence = private_dir(STATE_ROOT / state["project"] / "evidence")
    exp = expected()
    results, totals = {}, Decimal(0)
    for payload in invoices:
        invoice = payload["invoice"]
        kind = "subscription_invoice" if invoice.get("invoice_type") == "subscription" and invoice["fees_amount_cents"] == PLAN_FEE_CENTS \
            and all(f.get("fee_type", f.get("item", {}).get("type")) == "subscription" for f in invoice["fees"]) else "usage_invoice"
        source = evidence / f"lago-{kind}.json"
        source.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        (evidence / f"expected-{kind}.json").write_text(json.dumps(exp[kind], indent=2) + "\n", encoding="utf-8")
        actual = evidence / f"actual-{kind}.json"
        extracted = subprocess.run([sys.executable, str(SCRIPTS / "extract_actual.py"), str(source), "--output", str(actual)],
                                   capture_output=True, text=True)
        tested = subprocess.run([sys.executable, str(SCRIPTS / "money_test.py"), str(evidence / f"expected-{kind}.json"),
                                 str(actual), "--actual-source", str(source)], capture_output=True, text=True)
        results[kind] = {"invoice_lago_id": invoice["lago_id"], "number": invoice.get("number"),
                         "total_amount_cents": invoice["total_amount_cents"], "extract_exit": extracted.returncode,
                         "money_test_exit": tested.returncode, "money_test": tested.stdout.strip()[-800:] or extracted.stdout.strip()[-800:],
                         "ui_link": f"{state['ui_url']}/customer/{state['objects']['customer_lago_id']}/invoice/{invoice['lago_id']}/overview"}
        totals += Decimal(invoice["total_amount_cents"]) / 100
    replay = json.loads((evidence / "replay.json").read_text(encoding="utf-8"))
    passed = (set(results) == {"subscription_invoice", "usage_invoice"}
              and all(r["extract_exit"] == 0 and r["money_test_exit"] == 0 for r in results.values())
              and money(totals) == exp["period_total"] and replay["no_double_billing"])
    metadata = {"status": "LIVE_SELF_HOSTED_INVOICES_VALIDATED" if passed else "INCOMPLETE",
                "run_at": datetime.now(timezone.utc).isoformat(), "image": IMAGE, "project": state["project"],
                "isolation": state.get("isolation"), "objects": state["objects"], "replay": replay,
                "invoices": {k: {kk: vv for kk, vv in v.items() if kk != "ui_link"} for k, v in results.items()},
                "period_total": money(totals), "expected_period_total": exp["period_total"],
                "script_sha256": __import__("hashlib").sha256(Path(__file__).read_bytes()).hexdigest(),
                **source_provenance()}
    (evidence / "run-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"\n{'Live self-hosted validation complete' if passed else 'Live proof INCOMPLETE'}: "
          f"period total {money(totals)} USD (expected {exp['period_total']}).")
    for kind, result in results.items():
        print(f"  {kind}: {result['total_amount_cents']} cents, money test exit {result['money_test_exit']}")
        print(f"    {result['ui_link']}")
    print(f"  Sign in with the demo user stored in {STATE_ROOT / state['project'] / 'state.json'} (private).")
    print(f"  Evidence: {evidence}")
    print("This is a local demo. Production readiness is a separate gate.")
    if not passed:
        raise SystemExit(1)


def phase_teardown(args) -> None:
    state = load_state(args.project)
    require("teardown", args.approve)
    if not state["project"].startswith(PROJECT_PREFIX):
        raise SystemExit("Refusing to tear down a project the demo did not create.")
    docker("compose", "-p", state["project"], "-f", state["compose_file"], "down", "--volumes", "--remove-orphans")
    for path in sorted((STATE_ROOT / state["project"]).rglob("*"), reverse=True):
        path.unlink() if path.is_file() else path.rmdir()
    (STATE_ROOT / state["project"]).rmdir()
    print(f"Removed {state['project']} and its private state.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="phase", required=True)
    sub.add_parser("plan")
    up = sub.add_parser("up")
    up.add_argument("--approve")
    up.add_argument("--suffix", help="lowercase letters, digits, or dashes for the project name")
    for name in ("verify", "seed", "finalize", "teardown"):
        phase = sub.add_parser(name)
        phase.add_argument("--project", required=True)
        phase.add_argument("--approve")
    args = parser.parse_args()
    if getattr(args, "suffix", None) and not all(c.isalnum() or c == "-" for c in args.suffix.lower()):
        parser.error("--suffix may contain only letters, digits, and dashes")
    if getattr(args, "project", None) and not args.project.startswith(PROJECT_PREFIX):
        parser.error(f"--project must start with {PROJECT_PREFIX}")
    {"plan": phase_plan, "up": phase_up, "verify": phase_verify, "seed": phase_seed, "finalize": phase_finalize, "teardown": phase_teardown}[args.phase](args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
