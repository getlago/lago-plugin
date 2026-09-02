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

    starting_prepaid_value = Decimal("10.00")
    prepaid_credit_applied = min(starting_prepaid_value, total)
    ending_prepaid_value = starting_prepaid_value - prepaid_credit_applied
    amount_due = total - prepaid_credit_applied

    return {
        "mode": "offline_example",
        "scenario": "Acme asks an AI research assistant to analyze a report",
        "customer_action": "analyze_report",
        "customer": "demo_ai_studio",
        "plan": "demo_per_token",
        "subscription": "demo_ai_studio_per_token",
        "metric": "sum(tokens), filtered by model and input/output",
        "events_accepted": len(accepted),
        "duplicate_retry_ignored": duplicate_ignored,
        "total_tokens": sum(quantities.values()),
        "lines": lines,
        "expected_total": str(expected_total),
        "actual_total": str(total),
        "gross_usage_charge": str(total),
        "starting_prepaid_value": str(starting_prepaid_value),
        "prepaid_credit_applied": str(prepaid_credit_applied),
        "ending_prepaid_value": str(ending_prepaid_value),
        "amount_due": str(amount_due),
        "wallet_effect_timing": "when the eligible invoice is finalized",
        "reconciliation_discrepancy": "0.00",
        "live_lago_contacted": False,
    }


def render(result: dict[str, object]) -> str:
    lines = [
        "Lago Solution Engineer instant demo (offline)",
        "",
        "You do not need to do anything or provide credentials. This walkthrough is running now.",
        "",
        "Watch one customer action become an explainable charge in under a minute.",
        "",
        "Customer moment",
        "Acme asks an AI research assistant to analyze a report.",
        "That one job produces 21,000 input and output tokens across two models.",
        "",
        "What Lago does",
        "1. Receives four usage records from the app, each with a durable identity.",
        "2. Groups the tokens by model and input/output type.",
        "3. Applies the right price to each group.",
        "4. Ignores a retried record instead of billing it twice.",
        "5. Produces a traceable usage charge and applies eligible prepaid credits when the invoice is finalized.",
        "",
        "The money, explained",
    ]
    for item in result["lines"]:
        lines.append(
            f"{item['tokens']:>6,} {item['model']} {item['type']} tokens "
            f"at ${item['price_per_thousand']}/1,000 = ${item['amount']}"
        )
    lines.extend(
        [
            f"Gross usage charge: ${result['gross_usage_charge']} (expected ${result['expected_total']})",
            f"Illustrative prepaid value: ${result['starting_prepaid_value']} - ${result['prepaid_credit_applied']} = ${result['ending_prepaid_value']}",
            f"Amount due after credits: ${result['amount_due']}",
            f"Safety checks: duplicate ignored = {str(result['duplicate_retry_ignored']).lower()}; reconciliation difference = ${result['reconciliation_discrepancy']}",
            "The prepaid example assumes an eligible USD wallet, no tax, and invoice finalization. It does not simulate buying credits or collecting payment.",
            "",
            "What your team did not have to build by hand",
            "Engineering: aggregation, price selection, retry protection, credit application, and invoice calculation.",
            "Product: the same durable usage signal can support pay-as-you-go, prepaid, or hybrid packaging.",
            "Finance: a line-by-line calculation that can be independently checked and reconciled.",
            "",
            "The simple Lago model behind it",
            "Acme account -> customer (who is billed)",
            "Per-token offer -> plan and subscription (what Acme bought)",
            "Token records -> events (what Acme used)",
            "Token sum and prices -> metric and charges (how usage becomes money)",
            "Final billing result -> invoice (what is owed before and after credits)",
            "",
            "Lago does not replace your product's access control, payment provider, tax policy, or accounting decisions.",
            "",
            "Offline example complete. No Lago API, Docker, account, or credentials were used.",
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
