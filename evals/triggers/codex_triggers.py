#!/usr/bin/env python3
"""Measure implicit skill triggering in Codex; standard library only.

Codex has no plugin eval command, so each case runs `codex exec --json` in a
fresh, empty Git workspace with a read-only sandbox. A run counts as triggered
when the agent reads the skill's SKILL.md; it stops at that read or at the
timeout.

Default: install this checkout as `lago@lago-plugins` into a
temporary CODEX_HOME, the same path users take with `codex plugin add`. Only
auth.json is copied from the user's CODEX_HOME (mode 600), and the temporary
home is deleted afterwards. The user's own config and plugins are untouched.

`--project-skill`: copy the skill into `.agents/skills/implementation/` of each
workspace instead (https://learn.chatgpt.com/docs/build-skills). Faster, but the
skill is visible in the workspace, which biases toward triggering.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import shlex
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CASES = Path(__file__).resolve().parent
REPO = CASES.parents[1]
SKILL = REPO / "plugins/lago/skills/implementation"
FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.S)


def load_cases(pattern: str) -> list[tuple[str, str, str]]:
    cases = []
    for kind in ("positive", "negative"):
        for prompt in sorted((CASES / kind).glob(f"{pattern}/prompt.md")):
            body = FRONTMATTER.sub("", prompt.read_text(encoding="utf-8")).strip()
            cases.append((kind, prompt.parent.name, body))
    return cases


def install_plugin(codex_home: Path) -> None:
    source = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "auth.json"
    shutil.copyfile(source, codex_home / "auth.json")
    os.chmod(codex_home / "auth.json", 0o600)
    env = {**os.environ, "CODEX_HOME": str(codex_home)}
    for command in (["codex", "plugin", "marketplace", "add", str(REPO)], ["codex", "plugin", "add", "lago@lago-plugins"]):
        subprocess.run(command, env=env, check=True, capture_output=True, stdin=subprocess.DEVNULL)


def observed_read(event: dict, skill_path: Path) -> bool:
    """Conservative evidence: completed standalone cat and the complete file text.

    Other read forms are unclassified attempts, never a claimed successful load.
    This intentionally measures loading, not merely mentioning or attempting a read.
    The host may merge shell diagnostics with stdout; those do not erase a full read.
    """
    item = event.get("item") or {}
    if (event.get("type") != "item.completed"
            or item.get("type") != "command_execution"
            or item.get("status") != "completed" or item.get("exit_code") != 0):
        return False
    try:
        words = shlex.split(item.get("command") or "")
        if len(words) == 3 and Path(words[0]).name in ("sh", "bash", "zsh") and words[1] in ("-c", "-lc"):
            words = shlex.split(words[2])
    except ValueError:
        return False
    if len(words) == 3 and words[1] == "--":
        words.pop(1)
    expected = skill_path.read_text().strip()
    output = (item.get("aggregated_output") or "").strip()
    return (len(words) == 2 and words[0] in ("cat", "/bin/cat", "/usr/bin/cat")
            and Path(words[1]).is_absolute()
            and Path(words[1]).resolve() == skill_path.resolve()
            and bool(expected) and f"\n{expected}\n" in f"\n{output}\n")


def run_once(prompt: str, timeout: int, model: str | None, codex_home: Path | None) -> dict:
    with tempfile.TemporaryDirectory(prefix="lago-trigger-") as workspace:
        root = Path(workspace)
        if codex_home is None:
            skill_path = root / ".agents/skills/implementation/SKILL.md"
            shutil.copytree(SKILL, skill_path.parent)
        else:
            candidates = [p for p in codex_home.rglob("skills/implementation/SKILL.md")
                          if p.read_bytes() == (SKILL / "SKILL.md").read_bytes()]
            if len(candidates) != 1:
                return {"outcome": "error", "reason": "installed skill path is ambiguous or missing"}
            skill_path = candidates[0]
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        command = ["codex", "exec", "--json", "--ephemeral", "--sandbox", "read-only", "-C", workspace]
        if codex_home is None:
            command.append("--ignore-user-config")
        env = {**os.environ, "CODEX_HOME": str(codex_home)} if codex_home else None
        if model:
            command += ["-m", model]
        process = subprocess.Popen(command + [prompt], env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        expired = threading.Event()
        def expire():
            expired.set()
            process.kill()
        timer = threading.Timer(timeout, expire)
        timer.start()
        attempted = False
        try:
            for line in process.stdout:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                item = event.get("item") or {}
                attempted |= "SKILL.md" in (item.get("command") or "")
                if observed_read(event, skill_path):
                    return {"outcome": "loaded", "evidence": {
                        "command": item["command"], "exit_code": item["exit_code"],
                        "content_sha256": hashlib.sha256(skill_path.read_bytes()).hexdigest()}}
            process.wait()
            if expired.is_set():
                return {"outcome": "error", "reason": "timeout"}
            if process.returncode != 0:
                return {"outcome": "error", "reason": "process failed", "exit_code": process.returncode}
            if attempted:
                return {"outcome": "error", "reason": "skill read attempted but not verified"}
            return {"outcome": "not_loaded"}
        finally:
            timer.cancel()
            timer.join()
            if process.poll() is None:
                process.kill()
            process.wait()
            process.stdout.close()


def summarize_runs(runs: list[dict]) -> dict:
    totals = {kind: {"planned": 0, "completed": 0, "errors": 0, "loaded": 0}
              for kind in ("positive", "negative")}
    for run in runs:
        count = totals[run["kind"]]
        count["planned"] += 1
        if run["outcome"] == "error":
            count["errors"] += 1
        else:
            count["completed"] += 1
            count["loaded"] += run["outcome"] == "loaded"
    return {"coverage": totals, "complete": bool(runs) and all(v["errors"] == 0 for v in totals.values()),
            "hit_rate": "{loaded}/{completed}".format(**totals["positive"]),
            "false_trigger_rate": "{loaded}/{completed}".format(**totals["negative"]), "runs": runs}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", default="*", help="case directory glob")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("-j", "--concurrency", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--model")
    parser.add_argument("--project-skill", action="store_true", help="copy the skill into each workspace instead of installing the plugin")
    args = parser.parse_args()
    if min(args.runs, args.concurrency, args.timeout) < 1:
        parser.error("runs, concurrency and timeout must be positive")
    started_at = datetime.now(timezone.utc).isoformat()
    jobs = [(kind, name, prompt, attempt) for kind, name, prompt in load_cases(args.case) for attempt in range(1, args.runs + 1)]
    if not jobs:
        parser.error("no cases matched")
    with tempfile.TemporaryDirectory(prefix="lago-codex-home-") as home:
        codex_home = None if args.project_skill else Path(home)
        if codex_home:
            install_plugin(codex_home)
        with ThreadPoolExecutor(args.concurrency) as pool:
            outcomes = list(pool.map(lambda job: run_once(job[2], args.timeout, args.model, codex_home), jobs))
    runs = [{"kind": kind, "case": name, "attempt": attempt, **outcome}
            for (kind, name, _, attempt), outcome in zip(jobs, outcomes)]
    summary = summarize_runs(runs)
    summary.update({
        "started_at": started_at,
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "mode": "project-skill" if args.project_skill else "plugin lago@lago-plugins",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "source_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip()),
        "skill_sha256": hashlib.sha256((SKILL / "SKILL.md").read_bytes()).hexdigest(),
        "codex_version": subprocess.check_output(["codex", "--version"], text=True).strip(),
        "requested_model": args.model or "CLI default (not pinned)",
        "command": sys.argv,
    })
    print(json.dumps(summary, indent=2))
    return 0 if summary["complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
