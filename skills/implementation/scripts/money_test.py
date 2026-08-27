#!/usr/bin/env python3
"""Compare an independently calculated money test with a Lago result export."""

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

FIELDS = ("quantity", "unit_price", "subtotal", "discounts", "credits", "tax", "total")


def reject_constant(name: str) -> object:
    raise ValueError(f"non-finite JSON value {name} is not allowed in a money test")


def load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("expected", type=Path)
    parser.add_argument("actual", type=Path)
    args = parser.parse_args()
    expected, actual = load(args.expected), load(args.actual)
    mismatches = []
    if expected.get("currency") in (None, "") or actual.get("currency") in (None, ""):
        mismatches.append({"field": "currency", "error": "currency is required in both files"})
    elif expected.get("currency") != actual.get("currency"):
        mismatches.append({"field": "currency", "expected": expected.get("currency"), "actual": actual.get("currency")})
    for field in FIELDS:
        try:
            left, right = Decimal(str(expected[field])), Decimal(str(actual[field]))
        except (KeyError, InvalidOperation) as error:
            mismatches.append({"field": field, "error": str(error)})
            continue
        if left != right:
            mismatches.append({"field": field, "expected": str(left), "actual": str(right), "delta": str(right - left)})
    print(json.dumps({"status": "PASS" if not mismatches else "FAIL", "mismatches": mismatches}, indent=2))
    return 0 if not mismatches else 1


if __name__ == "__main__":
    sys.exit(main())
