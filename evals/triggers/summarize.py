#!/usr/bin/env python3
"""Summarize Claude trigger observations; incomplete evaluations exit nonzero."""
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
    totals = {kind: {"planned": 0, "completed": 0, "errors": 0, "fired": 0}
              for kind in ("positive", "negative")}
    observations = []
    problems = []
    seen = set()
    for case in result.get("cases", []):
        name = case["name"]
        kind = kind_of(name)
        if kind not in totals or name in seen:
            problems.append(f"unknown or duplicate case: {name}")
            continue
        seen.add(name)
        runs = case.get("arms", {}).get("with", [])
        planned = case.get("runsPerCase")
        if not isinstance(planned, int) or planned < 1:
            problems.append(f"missing planned run count: {name}")
            planned = len(runs)
        if len(runs) > planned:
            problems.append(f"extra runs: {name}")
        count = totals[kind]
        count["planned"] += max(planned, len(runs))
        expected = "fired" if kind == "positive" else "not-fired"
        for index in range(max(planned, len(runs))):
            run = runs[index] if index < len(runs) else {}
            graders = [g for g in run.get("graders", []) if g.get("name") == expected]
            error = run.get("error")
            valid = (len(graders) == 1 and isinstance(graders[0].get("passed"), bool)
                     and not graders[0].get("error") and not error)
            observation = {"case": name, "kind": kind, "attempt": index + 1}
            if not valid:
                count["errors"] += 1
                observation.update(outcome="error", reason=error or "missing or invalid activation grader")
            else:
                fired = graders[0]["passed"] if kind == "positive" else not graders[0]["passed"]
                count["completed"] += 1
                count["fired"] += fired
                observation.update(outcome="fired" if fired else "not_fired")
            observations.append(observation)
    if result.get("partial"):
        problems.append("source evaluation is partial")
    return {
        "claude_version": result.get("claudeVersion"),
        "coverage": totals,
        "complete": bool(observations) and not problems and all(v["errors"] == 0 for v in totals.values()),
        "problems": problems,
        "hit_rate": "{fired}/{completed}".format(**totals["positive"]),
        "false_trigger_rate": "{fired}/{completed}".format(**totals["negative"]),
        "misses": sorted({r["case"] for r in observations if r["kind"] == "positive" and r["outcome"] == "not_fired"}),
        "false_triggers": sorted({r["case"] for r in observations if r["kind"] == "negative" and r["outcome"] == "fired"}),
        "runs": observations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path, help="JSON written by claude plugin eval --json")
    args = parser.parse_args()
    summary = summarize(json.loads(args.result.read_text(encoding="utf-8")))
    print(json.dumps(summary, indent=2))
    return 0 if summary["complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
