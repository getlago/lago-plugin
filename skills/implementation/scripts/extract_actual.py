#!/usr/bin/env python3
"""Extract a hash-linked money-test result from a Lago API payload."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path


class ExtractionError(ValueError):
    """The payload cannot support the seven-field money test."""


CURRENCY = re.compile(r"^[A-Z]{3}$")


def reject_constant(name: str) -> object:
    raise ExtractionError(f"non-finite JSON value {name} is not allowed")


def decimal_value(value: object, field: str) -> Decimal:
    if isinstance(value, bool) or value in (None, ""):
        raise ExtractionError(f"{field} must be a finite number")
    try:
        parsed = Decimal(str(value))
    except InvalidOperation as error:
        raise ExtractionError(f"{field} must be a finite number") from error
    if not parsed.is_finite():
        raise ExtractionError(f"{field} must be a finite number")
    return parsed


def cents(value: object, field: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ExtractionError(f"{field} must be an integer number of cents")
    return Decimal(value) / Decimal(100)


def decimal_text(value: Decimal) -> str:
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered or "0"


def effective_unit_price(subtotal: Decimal, quantity: Decimal) -> Decimal:
    if quantity < 0:
        raise ExtractionError("quantity cannot be negative")
    if quantity == 0:
        if subtotal != 0:
            raise ExtractionError("cannot derive a unit price from zero quantity")
        return Decimal(0)
    with localcontext() as context:
        context.prec = 28
        return subtotal / quantity


def quantity_from_items(items: object, path: str) -> tuple[Decimal, set[str]]:
    if not isinstance(items, list) or not items:
        raise ExtractionError(f"{path} must be a non-empty array")
    quantity = Decimal(0)
    item_codes: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ExtractionError(f"{path}[{index}] must be an object")
        units = item.get("total_aggregated_units", item.get("units"))
        parsed_units = decimal_value(units, f"{path}[{index}].units")
        if parsed_units < 0:
            raise ExtractionError(f"{path}[{index}].units cannot be negative")
        quantity += parsed_units
        code = None
        if isinstance(item.get("billable_metric"), dict):
            code = item["billable_metric"].get("code")
        if code is None and isinstance(item.get("item"), dict):
            code = item["item"].get("code")
        if not code:
            raise ExtractionError(
                f"{path}[{index}] has no billable item code; do not combine unlabeled fees with usage"
            )
        item_codes.add(str(code))
    if len(item_codes) > 1:
        raise ExtractionError(
            "payload mixes multiple billable item codes; extract and compare each pricing dimension separately"
        )
    return quantity, item_codes


def extract_current_usage(usage: dict[str, object]) -> dict[str, object]:
    currency = usage.get("currency")
    if not isinstance(currency, str) or not CURRENCY.fullmatch(currency):
        raise ExtractionError("customer_usage.currency must be an uppercase three-letter code")
    subtotal = cents(usage.get("amount_cents"), "customer_usage.amount_cents")
    tax = cents(usage.get("taxes_amount_cents"), "customer_usage.taxes_amount_cents")
    total = cents(usage.get("total_amount_cents"), "customer_usage.total_amount_cents")
    if subtotal + tax != total:
        raise ExtractionError(
            "current usage total includes adjustments not exposed by this payload; use an invoice payload"
        )
    quantity, item_codes = quantity_from_items(
        usage.get("charges_usage"), "customer_usage.charges_usage"
    )
    unit_price = effective_unit_price(subtotal, quantity)
    return {
        "currency": currency,
        "quantity": decimal_text(quantity),
        "unit_price": decimal_text(unit_price),
        "subtotal": decimal_text(subtotal),
        "discounts": "0",
        "credits": "0",
        "tax": decimal_text(tax),
        "total": decimal_text(total),
        "_basis": {
            "quantity": "sum of current usage charge units",
            "unit_price": "effective subtotal divided by quantity",
            "item_code": next(iter(item_codes), None),
        },
    }


def extract_invoice(invoice: dict[str, object]) -> dict[str, object]:
    currency = invoice.get("currency")
    if not isinstance(currency, str) or not CURRENCY.fullmatch(currency):
        raise ExtractionError("invoice.currency must be an uppercase three-letter code")
    subtotal = cents(invoice.get("fees_amount_cents"), "invoice.fees_amount_cents")
    discounts = cents(
        invoice.get("coupons_amount_cents", 0), "invoice.coupons_amount_cents"
    )
    tax = cents(invoice.get("taxes_amount_cents"), "invoice.taxes_amount_cents")
    credit_components = {
        field: cents(invoice.get(field), f"invoice.{field}")
        for field in (
            "credit_notes_amount_cents",
            "prepaid_credit_amount_cents",
            "progressive_billing_credit_amount_cents",
        )
    }
    credits = sum(credit_components.values(), Decimal(0))
    total = cents(invoice.get("total_amount_cents"), "invoice.total_amount_cents")
    calculated_total = subtotal - discounts - credits + tax
    if calculated_total != total:
        raise ExtractionError(
            "invoice fields do not reconcile from explicit fees, coupons, credits, tax, and total"
        )
    quantity, item_codes = quantity_from_items(invoice.get("fees"), "invoice.fees")
    unit_price = effective_unit_price(subtotal, quantity)
    return {
        "currency": currency,
        "quantity": decimal_text(quantity),
        "unit_price": decimal_text(unit_price),
        "subtotal": decimal_text(subtotal),
        "discounts": decimal_text(discounts),
        "credits": decimal_text(credits),
        "tax": decimal_text(tax),
        "total": decimal_text(total),
        "_basis": {
            "quantity": "sum of invoice fee units",
            "unit_price": "effective subtotal divided by quantity",
            "credits": "credit notes + prepaid credits + progressive-billing credits",
            "credit_components": {
                field: decimal_text(value)
                for field, value in credit_components.items()
            },
            "item_code": next(iter(item_codes), None),
        },
    }


def extract(payload: object, source_sha256: str) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ExtractionError("Lago payload must be an object")
    if isinstance(payload.get("customer_usage"), dict):
        result = extract_current_usage(payload["customer_usage"])
        source_kind = "customer_usage"
        source_id = payload["customer_usage"].get("lago_invoice_id")
    elif isinstance(payload.get("invoice"), dict):
        result = extract_invoice(payload["invoice"])
        source_kind = "invoice"
        source_id = payload["invoice"].get("lago_id") or payload["invoice"].get("number")
    else:
        raise ExtractionError("expected a Lago customer_usage or invoice response payload")
    result["_evidence"] = {
        "generated_by": "extract_actual.py",
        "source_kind": source_kind,
        "source_id": source_id,
        "source_sha256": source_sha256,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", type=Path)
    parser.add_argument("--output", type=Path, help="declared output path; defaults to stdout")
    parser.add_argument("--max-bytes", type=int, default=10_000_000)
    args = parser.parse_args()
    try:
        size = args.payload.stat().st_size
        if size > args.max_bytes:
            raise ExtractionError(
                f"payload is {size} bytes; limit is {args.max_bytes} bytes"
            )
        raw = args.payload.read_bytes()
        payload = json.loads(raw, parse_constant=reject_constant)
        result = extract(payload, hashlib.sha256(raw).hexdigest())
        rendered = json.dumps(result, indent=2) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, ExtractionError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
