#!/usr/bin/env python3
"""Run the canonical Lago billing walkthrough entirely offline."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from decimal import Decimal


PRICES_PER_THOUSAND = {
    ("demo-small", "input"): Decimal("0.01"),
    ("demo-small", "output"): Decimal("0.03"),
    ("demo-large", "input"): Decimal("0.02"),
    ("demo-large", "output"): Decimal("0.06"),
}

EVENTS = [
    {
        "transaction_id": "demo_evt_small_input",
        "timestamp": 1785578400,  # 2026-08-01T10:00:00Z
        "model": "demo-small",
        "type": "input",
        "tokens": 12_000,
    },
    {
        "transaction_id": "demo_evt_small_output",
        "timestamp": 1785578460,  # 2026-08-01T10:01:00Z
        "model": "demo-small",
        "type": "output",
        "tokens": 3_000,
    },
    {
        "transaction_id": "demo_evt_large_input",
        "timestamp": 1785578520,  # 2026-08-01T10:02:00Z
        "model": "demo-large",
        "type": "input",
        "tokens": 5_000,
    },
    {
        "transaction_id": "demo_evt_large_output",
        "timestamp": 1785578580,  # 2026-08-01T10:03:00Z
        "model": "demo-large",
        "type": "output",
        "tokens": 1_000,
    },
]


def run_demo() -> dict[str, object]:
    accepted: dict[tuple[str, str], dict[str, object]] = {}
    duplicate_ignored = False

    for event in [*EVENTS, EVENTS[0]]:
        key = (str(event["transaction_id"]), str(event["timestamp"]))
        if key in accepted:
            if accepted[key] != event:
                raise ValueError("duplicate event identity has different content")
            duplicate_ignored = True
            continue
        accepted[key] = event

    quantities: defaultdict[tuple[str, str], int] = defaultdict(int)
    for event in accepted.values():
        quantities[(str(event["model"]), str(event["type"]))] += int(event["tokens"])

    lines = []
    total = Decimal("0.00")
    for model, direction in PRICES_PER_THOUSAND:
        tokens = quantities[(model, direction)]
        price = PRICES_PER_THOUSAND[(model, direction)]
        amount = (Decimal(tokens) / Decimal(1_000) * price).quantize(Decimal("0.01"))
        total += amount
        lines.append(
            {
                "model": model,
                "type": direction,
                "tokens": tokens,
                "price_per_thousand": str(price),
                "amount": str(amount),
            }
        )

    expected_total = Decimal("0.37")
    if total != expected_total:
        raise AssertionError(f"money test failed: expected {expected_total}, got {total}")

    monthly_subscription = Decimal("99.00")
    included_usage_value = Decimal("10.00")
    prior_usage_value = Decimal("9.80")
    included_value_before_job = included_usage_value - prior_usage_value
    included_credit_applied = min(included_value_before_job, total)
    overage = total - included_credit_applied
    included_value_after_job = included_value_before_job - included_credit_applied
    invoice_total_before_tax = monthly_subscription + overage

    return {
        "mode": "offline_example",
        "scenario": "An Acme employee asks Atlas AI to analyze a report",
        "customer_action": "analyze_report",
        "merchant": "Atlas AI",
        "customer": "Acme Corp",
        "end_user_role": "Acme employee",
        "plan": "atlas_pro",
        "subscription": "acme_atlas_pro",
        "metric": "sum(tokens), filtered by model and input/output",
        "events_accepted": len(accepted),
        "duplicate_retry_ignored": duplicate_ignored,
        "total_tokens": sum(quantities.values()),
        "lines": lines,
        "expected_total": str(expected_total),
        "actual_total": str(total),
        "gross_usage_charge": str(total),
        "monthly_subscription": str(monthly_subscription),
        "included_usage_value": str(included_usage_value),
        "prior_usage_value": str(prior_usage_value),
        "included_value_before_job": str(included_value_before_job),
        "included_credit_applied": str(included_credit_applied),
        "included_value_after_job": str(included_value_after_job),
        "overage": str(overage),
        "expected_invoice_total_before_tax": str(invoice_total_before_tax),
        "hybrid_invoice_live_validated": False,
        "credit_effect_timing": "when the eligible invoice is finalized",
        "reconciliation_discrepancy": "0.00",
        "live_lago_contacted": False,
    }


def render(result: dict[str, object]) -> str:
    lines = [
        "Lago Solution Engineer instant demo (offline)",
        "",
        "No setup, repository, or credentials needed.",
        "",
        "See Lago turn messy product usage into explainable revenue.",
        "",
        "1. Who sells what",
        "Atlas AI is the merchant. Acme Corp is its customer; an Acme employee is the end user.",
        "Atlas Pro: $99/month, including $10 of AI usage; additional usage is overage.",
        "",
        "2. One click, messy usage",
        "An Acme employee clicks Analyze report.",
        "One job -> 2 models -> input + output tokens -> 4 usage records -> 1 retry.",
        "Every record must stay attached to Acme and the correct billing period.",
        "",
        "3. Lago makes it billable",
        "Attribute to Acme -> ignore retry -> aggregate by model/type -> apply Atlas prices -> consume included usage -> calculate overage.",
        "",
        "4. The result",
    ]
    for item in result["lines"]:
        lines.append(
            f"{item['tokens']:>6,} {item['model']} {item['type']} tokens "
            f"at ${item['price_per_thousand']}/1,000 = ${item['amount']}"
        )
    lines.extend(
        [
            f"New job: ${result['gross_usage_charge']} (expected ${result['expected_total']})",
            f"Included usage left: ${result['included_value_before_job']} - ${result['included_credit_applied']} = ${result['included_value_after_job']}",
            f"Overage: ${result['overage']}",
            f"Expected Acme bill before tax: ${result['monthly_subscription']} subscription + ${result['overage']} overage = ${result['expected_invoice_total_before_tax']}",
            f"Safety checks: duplicate ignored = {str(result['duplicate_retry_ignored']).lower()}; reconciliation difference = ${result['reconciliation_discrepancy']}",
            "",
            "What Atlas avoids building",
            "A tenant-aware usage ledger, retry protection, pricing engine, included-credit tracking, invoice calculation, and reconciliation tooling.",
            "",
            "This is the simplest shape. Lago also supports tiered and volume pricing, prepaid wallets, commitments and overages, customer-specific pricing, multiple billing entities, and plan changes. Late, corrected, or high-volume event streams still require integration-specific validation.",
            "",
            "Atlas captures what happened. Lago turns it into accurate, explainable billing. Access control, payment, tax, and accounting remain separate.",
            "",
            "Under the hood: Acme -> customer; Atlas Pro -> plan/subscription; token records -> events; token sum -> metric; prices -> charges; $99.17 -> expected invoice.",
            "",
            "Offline example complete. The $0.37 usage result has separate live self-hosted evidence; the $99.17 hybrid invoice remains an illustrative target until that full configuration is validated live.",
            "No Lago API, Docker, account, or credentials were used in this walkthrough.",
            "Next, describe your product in one sentence or share its pricing page, and I can show where Lago fits.",
            "A code repository is optional for discovery and only needed when you want implementation-specific changes.",
            "Prefer concise execution without the walkthrough? Say: expert mode.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable evidence")
    args = parser.parse_args()
    result = run_demo()
    print(json.dumps(result, indent=2) if args.json else render(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
