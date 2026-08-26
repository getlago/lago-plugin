#!/usr/bin/env python3
"""Validate a synthetic Lago usage event offline."""

import argparse
import json
import math
import sys
from pathlib import Path


def validate(event: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(event, dict):
        return ["event must be an object"]
    for field in ("transaction_id", "external_subscription_id", "code", "timestamp"):
        if event.get(field) in (None, ""):
            errors.append(f"missing {field}")
    transaction_id = event.get("transaction_id")
    if isinstance(transaction_id, str) and transaction_id.lower().startswith(("random-", "uuid-")):
        errors.append("transaction_id appears retry-unstable")
    timestamp = event.get("timestamp")
    if timestamp is not None and (not isinstance(timestamp, (int, float)) or isinstance(timestamp, bool)):
        errors.append("timestamp must be Unix seconds as a number")
    properties = event.get("properties", {})
    if not isinstance(properties, dict):
        errors.append("properties must be an object")
    else:
        for key, value in properties.items():
            if isinstance(value, float) and not math.isfinite(value):
                errors.append(f"properties.{key} must be finite")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("event", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.event.read_text(encoding="utf-8"))
    event = payload.get("event", payload) if isinstance(payload, dict) else payload
    errors = validate(event)
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
