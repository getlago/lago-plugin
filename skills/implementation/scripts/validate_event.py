#!/usr/bin/env python3
"""Validate a synthetic Lago usage event offline."""

from __future__ import annotations

import argparse
import json
import math
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path


DEFAULT_NUMERIC_PROPERTIES = {"amount", "quantity", "tokens", "units", "value"}
DECIMAL = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")


def reject_constant(name: str) -> object:
    raise ValueError(f"non-finite JSON value {name} is not allowed")


def validate(
    event: object,
    numeric_properties: set[str] | None = None,
    allow_negative_properties: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    numeric_properties = numeric_properties or DEFAULT_NUMERIC_PROPERTIES
    allow_negative_properties = allow_negative_properties or set()
    if not isinstance(event, dict):
        return ["event must be an object"]
    for field in ("transaction_id", "external_subscription_id", "code"):
        value = event.get(field)
        if value in (None, ""):
            errors.append(f"missing {field}")
        elif not isinstance(value, str):
            errors.append(f"{field} must be a string")
    if event.get("timestamp") in (None, ""):
        errors.append("missing timestamp")
    transaction_id = event.get("transaction_id")
    if isinstance(transaction_id, str) and transaction_id.lower().startswith(
        ("random-", "uuid-")
    ):
        errors.append("transaction_id appears retry-unstable")
    timestamp = event.get("timestamp")
    if timestamp is not None:
        valid = isinstance(timestamp, int) and not isinstance(timestamp, bool)
        if isinstance(timestamp, str) and DECIMAL.fullmatch(timestamp):
            try:
                valid = Decimal(timestamp).is_finite()
            except InvalidOperation:
                valid = False
        if not valid:
            errors.append("timestamp must be Unix seconds as an integer or exact numeric string")

    precise_total = event.get("precise_total_amount_cents")
    if precise_total is not None:
        if not isinstance(precise_total, str) or not DECIMAL.fullmatch(precise_total):
            errors.append("precise_total_amount_cents must be an exact decimal string")
        elif Decimal(precise_total) < 0:
            errors.append("precise_total_amount_cents must be non-negative")
    properties = event.get("properties", {})
    if not isinstance(properties, dict):
        errors.append("properties must be an object")
    else:
        for key, value in properties.items():
            if value is None and key == "target_wallet_code":
                continue
            if isinstance(value, bool) or not isinstance(value, (str, int, float)):
                errors.append(f"properties.{key} must be a string or number")
                continue
            if isinstance(value, float) and not math.isfinite(value):
                errors.append(f"properties.{key} must be finite")
                continue
            if key in numeric_properties:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    errors.append(f"properties.{key} must be a number")
                    continue
                if not math.isfinite(value):
                    errors.append(f"properties.{key} must be finite")
                    continue
                if value < 0 and key not in allow_negative_properties:
                    errors.append(
                        f"properties.{key} must be non-negative unless the event contract explicitly allows corrections"
                    )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("event", type=Path)
    parser.add_argument(
        "--numeric-property",
        action="append",
        default=[],
        help="additional property that must be a finite number",
    )
    parser.add_argument(
        "--allow-negative-property",
        action="append",
        default=[],
        help="numeric property whose contract explicitly permits negative corrections",
    )
    parser.add_argument("--max-bytes", type=int, default=1_000_000)
    args = parser.parse_args()
    try:
        size = args.event.stat().st_size
        if size > args.max_bytes:
            raise ValueError(f"event file is {size} bytes; limit is {args.max_bytes} bytes")
        payload = json.loads(
            args.event.read_text(encoding="utf-8"), parse_constant=reject_constant
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(json.dumps({"status": "FAIL", "errors": [str(error)]}, indent=2))
        return 1
    event = payload.get("event", payload) if isinstance(payload, dict) else payload
    errors = validate(
        event,
        DEFAULT_NUMERIC_PROPERTIES | set(args.numeric_property),
        set(args.allow_negative_property),
    )
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
