#!/usr/bin/env python3
"""List external links for explicit release-time resolution checks."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import urlparse

TEXT_SUFFIXES = {".json", ".md", ".py", ".txt", ".yaml", ".yml"}
URL = re.compile(r"https?://[^\s<>\"')\]]+")


def links(root: Path, domains: set[str]) -> list[str]:
    found: set[str] = set()
    for path in sorted(root.rglob("*")):
        if (
            not path.is_file()
            or path.suffix.lower() not in TEXT_SUFFIXES
            or ".git" in path.parts
        ):
            continue
        text = path.read_text(encoding="utf-8")
        for value in URL.findall(text):
            value = value.rstrip(".,;:")
            host = (urlparse(value).hostname or "").lower()
            if not domains or any(
                host == domain or host.endswith(f".{domain}") for domain in domains
            ):
                found.add(value)
    return sorted(found)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--domain", action="append", default=[])
    args = parser.parse_args()
    for value in links(args.root.resolve(), {domain.lower() for domain in args.domain}):
        print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
