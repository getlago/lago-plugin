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
        "timestamp": "2026-08-01T10:00:00Z",
        "model": "demo-small",
        "type": "input",
        "tokens": 12_000,
    },
    {
        "transaction_id": "demo_evt_small_output",
        "timestamp": "2026-08-01T10:01:00Z",
        "model": "demo-small",
        "type": "output",
        "tokens": 3_000,
    },
    {
        "transaction_id": "demo_evt_large_input",
        "timestamp": "2026-08-01T10:02:00Z",
        "model": "demo-large",
        "type": "input",
        "tokens": 5_000,
    },
    {
        "transaction_id": "demo_evt_large_output",
        "timestamp": "2026-08-01T10:03:00Z",
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

    return {
        "mode": "offline_example",
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
        "reconciliation_discrepancy": "0.00",
        "live_lago_contacted": False,
    }


def render(result: dict[str, object]) -> str:
    lines = [
        "Lago Billing Engineer instant demo (offline)",
        "",
        "You do not need to do anything or provide credentials. This walkthrough is running now.",
        "",
        "Your product -> Lago",
        "AI Studio account -> customer",
        "Per-token offer -> plan and subscription",
        "Token records -> usage events",
        "Sum of tokens by model and input/output -> billable metric and charges",
        "",
        "Money test",
    ]
    for item in result["lines"]:
        lines.append(
            f"{item['tokens']:>6,} {item['model']} {item['type']} tokens "
            f"at ${item['price_per_thousand']}/1,000 = ${item['amount']}"
        )
    lines.extend(
        [
            f"Total: ${result['actual_total']} (expected ${result['expected_total']})",
            f"Duplicate retry ignored: {str(result['duplicate_retry_ignored']).lower()}",
            f"Reconciliation discrepancy: ${result['reconciliation_discrepancy']}",
            "",
            "Offline example complete. No Lago API, Docker, account, or credentials were used.",
            "When you want this applied to your product, open its repository and say: implement Lago.",
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
