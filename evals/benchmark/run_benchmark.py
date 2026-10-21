#!/usr/bin/env python3
"""Run the billing-correctness benchmark with and without the plugin; standard library only.

Results are private by design. Everything is written under --out, which must be
outside this repository, and nothing is uploaded: the eval report is never
published. The repository holds the method and tooling; results are shared only
by whoever runs it.

For each task in evals/benchmark/tasks/, `claude plugin eval` runs the same prompt
in two arms: with this plugin, and without any plugin. Each arm gets a fresh HOME
and config directory. The finished workspace of every run is copied out of the
harness's sealed temporary directory and scored by checks/score.py against a local
fake Lago API. Spend fields are dropped from everything written.

A run is "scored" when the scorer completed, and "error" when the agent run or the
scorer did not produce a workspace or a result. Errors are reported and are never
counted as passes or fails. The report is complete only when every planned run was
scored from a clean source tree that did not change during the run.

Usage: run_benchmark.py --out DIR [--runs N] [-j N] [--model MODEL] [--case GLOB]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
TASKS = HERE / "tasks"
sys.path.insert(0, str(HERE / "checks"))
sys.path.insert(0, str(REPO / "scripts"))
from score import CRITERIA, score  # noqa: E402
from plugin_eval import staged  # noqa: E402

SPEND_KEYS = {"costUsd", "judgeCostUsd", "cost_usd", "total_cost_usd"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        digest.update(path.relative_to(root).as_posix().encode() + b"\0" + path.read_bytes())
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def drop_spend(value):
    if isinstance(value, dict):
        return {k: drop_spend(v) for k, v in value.items() if k not in SPEND_KEYS}
    if isinstance(value, list):
        return [drop_spend(v) for v in value]
    return value


def unseal(kept: Path) -> Path | None:
    """The harness keeps a read-only run directory with its home sealed at mode 000."""
    sealed = kept / "sealed"
    if not sealed.is_dir():
        return None
    for path in (kept, sealed):
        path.chmod(stat.S_IRWXU)
    workspace = sealed / "home" / "cwd"
    return workspace if workspace.is_dir() else None


def remove(kept: Path) -> None:
    for path in [kept, *kept.rglob("*")]:
        try:
            if path.is_dir() and not path.is_symlink():
                path.chmod(stat.S_IRWXU)
        except OSError:
            pass
    shutil.rmtree(kept, ignore_errors=True)


def trace_model(trace: Path) -> str | None:
    try:
        with trace.open(encoding="utf-8") as handle:
            for line in handle:
                event = json.loads(line)
                if event.get("type") == "system" and event.get("subtype") == "init":
                    return event.get("model")
    except (OSError, ValueError):
        return None
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True, help="private output directory outside the repository")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("-j", "--concurrency", type=int, default=2)
    parser.add_argument("--model")
    parser.add_argument("--case", default="*")
    args = parser.parse_args()
    out = args.out.resolve()
    try:
        out.relative_to(REPO)
        parser.error("--out must be outside the repository; benchmark results are never committed")
    except ValueError:
        pass
    if min(args.runs, args.concurrency) < 1:
        parser.error("runs and concurrency must be positive")
    out.mkdir(parents=True, exist_ok=True)

    started = datetime.now(timezone.utc).isoformat()
    source_commit, source_dirty = git("rev-parse", "HEAD"), bool(git("status", "--porcelain"))
    claude_version = subprocess.check_output(["claude", "--version"], text=True).strip()
    eval_json = out / "eval-result.json"
    command = ["claude", "plugin", "eval", None, "--eval-dir", "evals/benchmark/tasks", "--case", args.case,
               "--scaffold", "--allow-tools", "Write", "Edit", "Bash", "--keep-temp", "--trust-plugin",
               "--no-publish", "--threshold", "0", "--runs", str(args.runs), "-j", str(args.concurrency),
               "--output-dir", str(out / "eval"), "--json", str(eval_json)]
    if args.model:
        command += ["--model", args.model]
    # Cases must sit inside the plugin folder; stage the shipped plugin with the tasks.
    with staged("evals/benchmark/tasks") as plugin:
        command[3] = str(plugin)
        completed = subprocess.run(command, cwd=REPO, capture_output=True, text=True)
    (out / "eval.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    if not eval_json.is_file():
        print(json.dumps({"complete": False, "reason": "claude plugin eval produced no result", "exit_code": completed.returncode}))
        return 1
    result = drop_spend(json.loads(eval_json.read_text(encoding="utf-8")))
    eval_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    runs = []
    for case in result.get("cases", []):
        for arm in ("with", "without"):
            for attempt, run in enumerate(case.get("arms", {}).get(arm, []), start=1):
                record = {"case": case["name"], "arm": arm, "attempt": attempt, "agent_error": run.get("error"),
                          "turns": run.get("turns"), "duration_seconds": run.get("durationSeconds")}
                trace = Path(run["tracePath"]) if run.get("tracePath") else None
                kept = trace.parents[1] if trace else None
                record["model"] = trace_model(trace) if trace else None
                workspace = unseal(kept) if kept and kept.is_dir() else None
                if workspace is None:
                    record.update(status="error", reason="no finished workspace was kept")
                else:
                    copy = out / "workspaces" / f"{case['name']}-{arm}-{attempt}"
                    shutil.rmtree(copy, ignore_errors=True)
                    shutil.copytree(workspace, copy, symlinks=True, ignore=shutil.ignore_patterns(".git", "node_modules"))
                    scored = score(copy)
                    record.update(status=scored["status"], workspace=str(copy.relative_to(out)))
                    if scored["status"] == "scored":
                        record["criteria"] = scored["criteria"]
                        record["timed_out"] = scored["timed_out"]
                    else:
                        record["reason"] = scored.get("reason")
                if kept and kept.is_dir():
                    remove(kept)
                runs.append(record)

    summary = {}
    for arm in ("with", "without"):
        arm_runs = [r for r in runs if r["arm"] == arm]
        scored_runs = [r for r in arm_runs if r["status"] == "scored"]
        summary[arm] = {
            "planned": len(arm_runs), "scored": len(scored_runs), "errors": len(arm_runs) - len(scored_runs),
            "all_criteria_passed": sum(all(v["result"] == "pass" for v in r["criteria"].values()) for r in scored_runs),
            "criteria": {c: sum(r["criteria"][c]["result"] == "pass" for r in scored_runs) for c in CRITERIA},
        }
    end_commit, end_dirty = git("rev-parse", "HEAD"), bool(git("status", "--porcelain"))
    report = {
        "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": source_commit, "source_dirty": source_dirty,
        "source_changed": (end_commit, end_dirty) != (source_commit, source_dirty),
        "claude_version": claude_version, "requested_model": args.model,
        "observed_models": sorted({r["model"] for r in runs if r.get("model")}),
        "runner_sha256": sha256(Path(__file__)), "scorer_sha256": tree_sha256(HERE / "checks"),
        "tasks_sha256": tree_sha256(TASKS), "runs_per_arm": args.runs,
        "summary": summary, "runs": runs,
    }
    planned = sum(s["planned"] for s in summary.values())
    report["complete"] = (planned > 0 and all(s["errors"] == 0 for s in summary.values())
                          and not source_dirty and not report["source_changed"])
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(out / "report.json"), "complete": report["complete"], "summary": summary}, indent=2))
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
