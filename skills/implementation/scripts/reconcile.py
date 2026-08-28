#!/usr/bin/env python3
"""Read-only CSV reconciliation by stable key and amount."""

import argparse
import csv
import json
import sys
from decimal import Decimal
from pathlib import Path


def rows(path: Path, key: str) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        result = {}
        for row in csv.DictReader(handle):
            value = row.get(key)
            if not value:
                raise ValueError(f"missing {key} in {path}")
            if value in result:
                raise ValueError(f"duplicate {key}={value} in {path}")
            result[value] = row
        return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("lago", type=Path)
    parser.add_argument("--key", default="external_id")
    parser.add_argument("--amount", default="amount")
    args = parser.parse_args()
    source, lago = rows(args.source, args.key), rows(args.lago, args.key)
    counts = {"source_rows": len(source), "lago_rows": len(lago)}
    if not source or not lago:
        print(json.dumps({"status": "FAIL", "error": "nothing to reconcile: one side has zero rows", "counts": counts}, indent=2))
        return 1
    discrepancies = []
    for value in sorted(source.keys() | lago.keys()):
        if value not in lago:
            discrepancies.append({"key": value, "class": "missing in Lago"})
        elif value not in source:
            discrepancies.append({"key": value, "class": "missing in source"})
        elif Decimal(source[value][args.amount]) != Decimal(lago[value][args.amount]):
            discrepancies.append({"key": value, "class": "amount mismatch", "source": source[value][args.amount], "lago": lago[value][args.amount]})
    print(json.dumps({"status": "PASS" if not discrepancies else "DIFFERENCES", "counts": counts, "discrepancies": discrepancies}, indent=2))
    return 0 if not discrepancies else 2


if __name__ == "__main__":
    sys.exit(main())
