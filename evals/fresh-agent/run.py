#!/usr/bin/env python3
"""Run START_HERE against fresh agents, with no plugin and explicit fetch domains.

Results are private and must stay outside the repository. The guide URL is pinned
to HEAD; push the candidate first. See https://code.claude.com/docs/en/plugin-evals
for why an unqualified WebFetch grant does not grant shell network access.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SUITE = Path(__file__).resolve().parent / "nextjs-start-here"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--runs", type=int, default=5)
    args = parser.parse_args()
    out = args.out.resolve()
    if out == REPO or REPO in out.parents or out.exists():
        parser.error("--out must be a new directory outside the repository")
    if args.runs < 1 or args.runs > 50:
        parser.error("--runs must be between 1 and 50")
    if git("status", "--porcelain"):
        parser.error("commit the candidate before collecting release evidence")
    commit = git("rev-parse", "HEAD")
    with tempfile.TemporaryDirectory(prefix="lago-fresh-") as directory:
        root = Path(directory)
        case = root / "evals/nextjs-start-here"
        shutil.copytree(SUITE, case, ignore=shutil.ignore_patterns("node_modules", "results", "__pycache__"))
        prompt = case / "prompt.md"
        prompt.write_text(prompt.read_text().replace("/main/START_HERE.md", f"/{commit}/START_HERE.md"))
        command = ["claude", "plugin", "eval", str(root), "--ablation", "none", "--runs", str(args.runs),
                   "--model", args.model, "--judge-model", args.model, "-j", "2", "--scaffold",
                   "--allow-tools", "Bash", "Write", "Edit", "WebFetch(domain:raw.githubusercontent.com)",
                   "WebFetch(domain:registry.npmjs.org)", "WebFetch(domain:getlago.com)",
                   "--disallow-tools", "Agent", "TaskStop", "--trust-plugin", "--no-publish", "--keep-temp",
                   "--output-dir", str(out)]
        result = subprocess.run(command, cwd=REPO)
    aggregate = out / "aggregate-result.json"
    summary = {"source_commit": commit, "source_changed": git("rev-parse", "HEAD") != commit or bool(git("status", "--porcelain")),
               "cli_version": subprocess.check_output(["claude", "--version"], text=True).strip(),
               "requested_model": args.model, "plugin_loaded": False, "planned": args.runs, "runs": []}
    if aggregate.exists():
        data = json.loads(aggregate.read_text())
        for case in data.get("cases", []):
            for index, run in enumerate(case.get("arms", {}).get("with", []), 1):
                models = set()
                lago_loaded = False
                trace = Path(run.get("tracePath", ""))
                if trace.is_file():
                    for line in trace.read_text().splitlines():
                        entry = json.loads(line)
                        if entry.get("type") == "system" and entry.get("subtype") == "init":
                            if isinstance(entry.get("model"), str) and entry["model"]:
                                models.add(entry["model"])
                            lago_loaded |= any(p.get("name") == "lago" for p in entry.get("plugins", []))
                summary["runs"].append({"attempt": index, "models": sorted(m for m in models if m),
                    "complete": not run.get("error") and bool(models) and not lago_loaded, "lago_loaded": lago_loaded, "error": run.get("error"),
                    "passed": bool(run.get("passed")) and not run.get("error"),
                    "failed_checks": [g["name"] for g in run.get("graders", []) if not g.get("passed")]})
    summary["plugin_loaded"] = any(r["lago_loaded"] for r in summary["runs"])
    summary["complete"] = (len(summary["runs"]) == args.runs and not summary["source_changed"]
                           and all(r["complete"] for r in summary["runs"]))
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return result.returncode or (0 if summary["complete"] and all(r["passed"] for r in summary["runs"]) else 1)


if __name__ == "__main__":
    raise SystemExit(main())
