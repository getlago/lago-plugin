#!/usr/bin/env python3
"""Summarize a `claude plugin eval --json` trigger run; standard library only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CASES = Path(__file__).resolve().parent


def kind_of(name: str) -> str:
    for kind in ("positive", "negative"):
        if (CASES / kind / name).is_dir():
            return kind
    return "unknown"


def summarize(result: dict) -> dict:
    totals = {"positive": [0, 0], "negative": [0, 0]}
    misses: list[str] = []
    false_fires: list[str] = []
    for case in result.get("cases", []):
        kind = kind_of(case["name"])
        if kind not in totals:
            continue
        for run in case.get("arms", {}).get("with", []):
            if not run.get("graders"):  # turn-capped runs still carry grader results
                continue
            passed = all(grader.get("passed") for grader in run.get("graders", []))
            fired = passed if kind == "positive" else not passed
            totals[kind][0] += int(fired)
            totals[kind][1] += 1
            if kind == "positive" and not fired:
                misses.append(case["name"])
            if kind == "negative" and fired:
                false_fires.append(case["name"])
    positive_fired, positive_runs = totals["positive"]
    negative_fired, negative_runs = totals["negative"]
    return {
        "claude_version": result.get("claudeVersion"),
        "hit_rate": f"{positive_fired}/{positive_runs}",
        "false_trigger_rate": f"{negative_fired}/{negative_runs}",
        "misses": sorted(set(misses)),
        "false_triggers": sorted(set(false_fires)),
        "cost_usd": round(result.get("costUsd") or 0, 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path, help="JSON written by claude plugin eval --json")
    args = parser.parse_args()
    print(json.dumps(summarize(json.loads(args.result.read_text(encoding="utf-8"))), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
