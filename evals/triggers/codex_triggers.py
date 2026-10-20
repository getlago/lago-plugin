#!/usr/bin/env python3
"""Measure implicit skill triggering in Codex; standard library only.

Codex has no plugin eval command, so each case runs `codex exec --json` in a
fresh, empty Git workspace with a read-only sandbox. A run counts as triggered
when the agent reads the skill's SKILL.md; it stops at that read or at the
timeout.

Default (`--plugin`): install this checkout as `lago@lago-plugins` into a
temporary CODEX_HOME, the same path users take with `codex plugin add`. Only
auth.json is copied from the user's CODEX_HOME (mode 600), and the temporary
home is deleted afterwards. The user's own config and plugins are untouched.

`--project-skill`: copy the skill into `.agents/skills/implementation/` of each
workspace instead (https://learn.chatgpt.com/docs/build-skills). Faster, but the
skill is visible in the workspace, which biases toward triggering.
"""

from __future__ import annotations

import argparse
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
SKILL = REPO / "skills/implementation"
READ_SKILL = re.compile(r"implementation/SKILL\.md")
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


def run_once(prompt: str, timeout: int, model: str | None, codex_home: Path | None) -> bool | None:
    with tempfile.TemporaryDirectory(prefix="lago-trigger-") as workspace:
        root = Path(workspace)
        if codex_home is None:
            shutil.copytree(SKILL, root / ".agents/skills/implementation")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        command = ["codex", "exec", "--json", "--ephemeral", "--sandbox", "read-only", "-C", workspace]
        if codex_home is None:
            command.append("--ignore-user-config")
        env = {**os.environ, "CODEX_HOME": str(codex_home)} if codex_home else None
        if model:
            command += ["-m", model]
        process = subprocess.Popen(command + [prompt], env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        timer = threading.Timer(timeout, process.kill)
        timer.start()
        try:
            for line in process.stdout:
                try:
                    item = json.loads(line).get("item") or {}
                except json.JSONDecodeError:
                    continue
                if item.get("type") == "command_execution" and READ_SKILL.search(item.get("command") or ""):
                    process.kill()
                    return True
            process.wait()
            return False if process.returncode == 0 else None
        finally:
            timer.cancel()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", default="*", help="case directory glob")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("-j", "--concurrency", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--model")
    parser.add_argument("--project-skill", action="store_true", help="copy the skill into each workspace instead of installing the plugin")
    args = parser.parse_args()
    jobs = [(kind, name, prompt) for kind, name, prompt in load_cases(args.case) for _ in range(args.runs)]
    with tempfile.TemporaryDirectory(prefix="lago-codex-home-") as home:
        codex_home = None if args.project_skill else Path(home)
        if codex_home:
            install_plugin(codex_home)
        with ThreadPoolExecutor(args.concurrency) as pool:
            fired = list(pool.map(lambda job: run_once(job[2], args.timeout, args.model, codex_home), jobs))
    totals = {"positive": [0, 0], "negative": [0, 0]}
    misses, false_fires, errors = set(), set(), set()
    for (kind, name, _), result in zip(jobs, fired):
        if result is None:
            errors.add(name)
            continue
        totals[kind][0] += int(result)
        totals[kind][1] += 1
        if kind == "positive" and not result:
            misses.add(name)
        if kind == "negative" and result:
            false_fires.add(name)
    print(json.dumps({
        "mode": "project-skill" if args.project_skill else "plugin lago@lago-plugins",
        "hit_rate": "{}/{}".format(*totals["positive"]),
        "false_trigger_rate": "{}/{}".format(*totals["negative"]),
        "misses": sorted(misses),
        "false_triggers": sorted(false_fires),
        "errors": sorted(errors),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
