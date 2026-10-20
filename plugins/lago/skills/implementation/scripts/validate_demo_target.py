#!/usr/bin/env python3
"""Fail closed unless a seeded demo target is an explicit local endpoint."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
from urllib.parse import urlparse


PROJECT = re.compile(r"^lago-plugin-demo-[a-z0-9][a-z0-9_-]{2,40}$")


def validate(url: str, compose_project: str) -> list[str]:
    errors: list[str] = []
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        errors.append("URL scheme must be http or https")
    if parsed.username or parsed.password:
        errors.append("URL must not contain credentials")
    if parsed.query or parsed.fragment:
        errors.append("URL must not contain a query or fragment")
    if parsed.path not in {"", "/", "/api/v1", "/api/v1/"}:
        errors.append("URL path must be empty or /api/v1")
    try:
        port = parsed.port
    except ValueError:
        port = None
        errors.append("URL port is invalid")
    if port is None:
        errors.append("URL must declare the dedicated local port explicitly")

    host = (parsed.hostname or "").rstrip(".").lower()
    is_loopback = host == "localhost"
    if host:
        try:
            is_loopback = is_loopback or ipaddress.ip_address(host).is_loopback
        except ValueError:
            pass
    if not is_loopback:
        errors.append("seeded demos require localhost or a loopback IP; remote targets are forbidden")
    if not PROJECT.fullmatch(compose_project):
        errors.append(
            "Compose project must use a dedicated lago-plugin-demo-<suffix> name"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="self-hosted Lago base URL")
    parser.add_argument("--compose-project", required=True)
    args = parser.parse_args()
    errors = validate(args.url, args.compose_project)
    print(
        json.dumps(
            {
                "status": "PASS" if not errors else "FAIL",
                "target": args.url,
                "compose_project": args.compose_project,
                "errors": errors,
            },
            indent=2,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
