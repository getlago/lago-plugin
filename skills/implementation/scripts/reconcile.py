#!/usr/bin/env python3
"""Read-only CSV reconciliation by stable key, currency, and amount."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path


class StructuralError(ValueError):
    """Input cannot support a trustworthy reconciliation."""


def read_rows(
    path: Path, key: str, amount: str, currency: str, side: str, max_bytes: int
) -> tuple[dict[str, dict[str, str]], int, list[dict[str, object]]]:
    try:
        size = path.stat().st_size
        if size > max_bytes:
            raise StructuralError(
                f"{side} CSV is {size} bytes; limit is {max_bytes} bytes"
            )
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            headers = reader.fieldnames or []
            for required in (key, amount, currency):
                if required not in headers:
                    raise StructuralError(f"{side} CSV is missing required column: {required}")
            result: dict[str, dict[str, str]] = {}
            key_counts: Counter[str] = Counter()
            row_count = 0
            for index, row in enumerate(reader, start=2):
                row_count += 1
                value = (row.get(key) or "").strip()
                if not value:
                    raise StructuralError(f"{side} CSV row {index} is missing {key}")
                raw_amount = (row.get(amount) or "").strip()
                raw_currency = (row.get(currency) or "").strip().upper()
                if not raw_amount:
                    raise StructuralError(f"{side} CSV row {index} is missing {amount}")
                if not raw_currency:
                    raise StructuralError(f"{side} CSV row {index} is missing {currency}")
                try:
                    parsed_amount = Decimal(raw_amount)
                except InvalidOperation as error:
                    raise StructuralError(
                        f"{side} CSV row {index} has invalid {amount}: {raw_amount}"
                    ) from error
                if not parsed_amount.is_finite():
                    raise StructuralError(
                        f"{side} CSV row {index} has non-finite {amount}: {raw_amount}"
                    )
                key_counts[value] += 1
                if value not in result:
                    result[value] = {**row, amount: raw_amount, currency: raw_currency}
    except StructuralError:
        raise
    except (OSError, UnicodeError, csv.Error) as error:
        raise StructuralError(f"cannot read {side} CSV {path}: {error}") from error

    duplicates = [
        {"key": value, "class": "duplicate key", "side": side, "count": count}
        for value, count in sorted(key_counts.items())
        if count > 1
    ]
    return result, row_count, duplicates


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("lago", type=Path)
    parser.add_argument("--key", default="external_id")
    parser.add_argument("--amount", default="amount")
    parser.add_argument("--currency", default="currency")
    parser.add_argument("--max-bytes", type=int, default=50_000_000)
    args = parser.parse_args()

    try:
        source, source_count, source_duplicates = read_rows(
            args.source, args.key, args.amount, args.currency, "source", args.max_bytes
        )
        lago, lago_count, lago_duplicates = read_rows(
            args.lago, args.key, args.amount, args.currency, "Lago", args.max_bytes
        )
    except StructuralError as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, indent=2))
        return 1

    counts = {
        "source_rows": source_count,
        "source_unique_keys": len(source),
        "lago_rows": lago_count,
        "lago_unique_keys": len(lago),
    }
    if not source or not lago:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "error": "nothing to reconcile: one side has zero rows",
                    "counts": counts,
                },
                indent=2,
            )
        )
        return 1

    discrepancies = [*source_duplicates, *lago_duplicates]
    for value in sorted(source.keys() | lago.keys()):
        if value not in lago:
            discrepancies.append({"key": value, "class": "missing in Lago"})
            continue
        if value not in source:
            discrepancies.append({"key": value, "class": "missing in source"})
            continue
        if source[value][args.currency] != lago[value][args.currency]:
            discrepancies.append(
                {
                    "key": value,
                    "class": "currency mismatch",
                    "source": source[value][args.currency],
                    "lago": lago[value][args.currency],
                }
            )
            continue
        if Decimal(source[value][args.amount]) != Decimal(lago[value][args.amount]):
            discrepancies.append(
                {
                    "key": value,
                    "class": "amount mismatch",
                    "source": source[value][args.amount],
                    "lago": lago[value][args.amount],
                }
            )

    print(
        json.dumps(
            {
                "status": "PASS" if not discrepancies else "DIFFERENCES",
                "counts": counts,
                "discrepancies": discrepancies,
            },
            indent=2,
        )
    )
    return 0 if not discrepancies else 2


if __name__ == "__main__":
    raise SystemExit(main())
