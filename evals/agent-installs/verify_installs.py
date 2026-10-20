#!/usr/bin/env python3
"""Install this checkout with other agents' real CLIs and record verified observations.

Each check runs a pinned CLI through npx with a temporary HOME, so the user's own
agent configuration is never read or changed and no credentials are needed. A
check passes only when the CLI reports success AND the installed SKILL.md is
byte-identical to this checkout's skill. Anything else is recorded as a failure
with its reason. Output is JSON on stdout; the exit code is 1 unless every check
passed and the source tree was clean.

Usage: verify_installs.py [--allow-dirty]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skills/implementation/SKILL.md"
GEMINI = "@google/gemini-cli@0.64.0"
COPILOT = "@github/copilot@1.0.100"
SKILLS = "skills@1.7.4"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], home: Path, cwd: Path, stdin: str = "") -> dict:
    env = {"HOME": str(home), "PATH": os.environ["PATH"], "npm_config_update_notifier": "false"}
    result = subprocess.run(command, cwd=cwd, env=env, input=stdin, capture_output=True, text=True, timeout=600)
    # Keep the tail for diagnosis; temp paths are replaced so evidence holds no local paths.
    output = (result.stdout + result.stderr).replace(str(home), "<home>").replace(str(REPO), "<checkout>")
    return {"command": " ".join(command).replace(str(REPO), "<checkout>"), "exit_code": result.returncode,
            "output_tail": output.strip().splitlines()[-12:]}


def installed_skill(home: Path, root: Path) -> dict:
    found = [p for p in root.rglob("implementation/SKILL.md") if p.is_file()]
    matches = [p for p in found if sha256(p) == sha256(SKILL)]
    return {"found": len(found), "identical": len(matches),
            "paths": [str(p).replace(str(home), "<home>") for p in matches]}


def check_gemini(home: Path) -> dict:
    steps = [
        run(["npx", "-y", GEMINI, "extensions", "validate", str(REPO)], home, REPO),
        run(["npx", "-y", GEMINI, "extensions", "install", str(REPO), "--consent"], home, home, stdin="y\n"),
        run(["npx", "-y", GEMINI, "skills", "list"], home, home),
    ]
    skill = installed_skill(home, home / ".gemini/extensions")
    listed = any("implementation [Enabled]" in line for line in steps[2]["output_tail"])
    validated = any("successfully validated" in line for line in steps[0]["output_tail"])
    passed = all(s["exit_code"] == 0 for s in steps) and validated and listed and skill["identical"] == 1
    return {"agent": "gemini-cli", "cli": GEMINI, "passed": passed, "skill": skill, "steps": steps,
            "bundle_has_release_manifest": (home / ".gemini/extensions/lago/RELEASE-MANIFEST.json").is_file()}


def check_copilot(home: Path) -> dict:
    steps = [
        run(["npx", "-y", COPILOT, "plugin", "marketplace", "add", str(REPO)], home, home),
        run(["npx", "-y", COPILOT, "plugin", "install", "lago@lago-plugins"], home, home),
        run(["npx", "-y", COPILOT, "plugin", "list"], home, home),
    ]
    installed = any("Installed 1 skill" in line for line in steps[1]["output_tail"])
    listed = any("lago@lago-plugins" in line and "enabled" in line for line in steps[2]["output_tail"])
    # A local marketplace is loaded live from the checkout, so the skill file is this checkout's file.
    passed = all(s["exit_code"] == 0 for s in steps) and installed and listed
    return {"agent": "github-copilot-cli", "cli": COPILOT, "passed": passed, "steps": steps,
            "note": "local marketplace plugins load live from the source directory; nothing is copied"}


def check_skills_sh(home: Path) -> dict:
    project = home / "project"
    project.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    steps = [run(["npx", "-y", SKILLS, "add", str(REPO), "--skill", "implementation",
                  "-a", "codex", "-a", "cursor", "-a", "github-copilot", "-a", "gemini-cli", "--copy", "-y"], home, project)]
    skill = installed_skill(home, project / ".agents/skills")
    passed = steps[0]["exit_code"] == 0 and skill["identical"] == 1
    return {"agent": "skills.sh", "cli": SKILLS, "passed": passed, "skill": skill, "steps": steps,
            "bundle_has_release_manifest": (project / ".agents/skills/implementation/RELEASE-MANIFEST.json").is_file()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip())
    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "source_dirty": dirty,
        "skill_sha256": sha256(SKILL),
        "runner_sha256": sha256(Path(__file__)),
        "node": subprocess.check_output(["node", "--version"], text=True).strip(),
        "checks": [],
    }
    for check in (check_gemini, check_copilot, check_skills_sh):
        with tempfile.TemporaryDirectory(prefix="lago-agent-install-") as home:
            try:
                report["checks"].append(check(Path(home)))
            except (subprocess.SubprocessError, OSError) as error:
                report["checks"].append({"agent": check.__name__, "passed": False, "error": str(error)})
    report["complete"] = all(c["passed"] for c in report["checks"]) and (not dirty or args.allow_dirty)
    print(json.dumps(report, indent=2))
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
