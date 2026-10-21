#!/usr/bin/env python3
"""Install this checkout with other agents' real CLIs and record verified observations.

Each check runs a pinned CLI through npx with a temporary HOME, so the user's own
agent configuration is never read or changed and no credentials are needed. A
check passes only when discovery and skill identity are verified. Full-bundle
installs must also pass release integrity and the offline demo. Anything else is recorded as a failure
with its reason. Output is JSON on stdout; the exit code is 1 unless every check
passed and the source tree was clean.

Usage: verify_installs.py [--allow-dirty] (development only; never clean evidence)
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PLUGIN = REPO / "plugins/lago"
RELEASE = REPO / "tools/release"
SKILL = PLUGIN / "skills/implementation/SKILL.md"
GEMINI = "@google/gemini-cli@0.64.0"
COPILOT = "@github/copilot@1.0.100"
SKILLS = "skills@1.7.4"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sanitize(text: str, home: Path) -> str:
    # Resolve macOS temporary-directory aliases as well as the supplied paths.
    for path, replacement in ((home, "<home>"), (REPO, "<checkout>")):
        for alias in sorted({str(path), str(path.resolve())}, key=len, reverse=True):
            text = text.replace(alias, replacement)
    return text.replace(sys.executable, "python3")


def verify_bundle(root: Path) -> dict:
    # Use the reviewed checkout's verifier, not unverified installed code.
    # The manifest lives with the release tooling, outside the shipped plugin.
    spec = importlib.util.spec_from_file_location("install_integrity", RELEASE / "release_integrity.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        return module.check(root, RELEASE / "RELEASE-MANIFEST.json")
    except (OSError, ValueError) as error:
        return {"status": "FAIL", "error": type(error).__name__}


def verify_demo(root: Path, home: Path, integrity: dict) -> dict:
    if integrity["status"] != "PASS":
        return {"passed": False, "reason": "not executed: bundle integrity failed"}
    step = run([sys.executable, str(root / "skills/implementation/scripts/run_demo.py"), "--json"], home, home)
    return {"passed": step["exit_code"] == 0, "step": step}


def run(command: list[str], home: Path, cwd: Path, stdin: str = "") -> dict:
    env = {"HOME": str(home), "PATH": os.environ["PATH"], "npm_config_update_notifier": "false"}
    result = subprocess.run(command, cwd=cwd, env=env, input=stdin, capture_output=True, text=True, timeout=600)
    # Keep the tail for diagnosis; temp paths are replaced so evidence holds no local paths.
    output = sanitize(result.stdout + result.stderr, home)
    return {"command": sanitize(" ".join(command), home), "exit_code": result.returncode,
            "output_tail": output.strip().splitlines()[-12:]}


def installed_skill(home: Path, root: Path) -> dict:
    found = [p for p in root.rglob("implementation/SKILL.md") if p.is_file()]
    matches = [p for p in found if sha256(p) == sha256(SKILL)]
    return {"found": len(found), "identical": len(matches),
            "paths": [sanitize(str(p), home) for p in matches]}


def check_gemini(home: Path) -> dict:
    steps = [
        run(["npx", "-y", GEMINI, "extensions", "validate", str(PLUGIN)], home, REPO),
        run(["npx", "-y", GEMINI, "extensions", "install", str(PLUGIN), "--consent"], home, home, stdin="y\n"),
        run(["npx", "-y", GEMINI, "skills", "list"], home, home),
    ]
    skill = installed_skill(home, home / ".gemini/extensions")
    listed = any("implementation [Enabled]" in line for line in steps[2]["output_tail"])
    validated = any("successfully validated" in line for line in steps[0]["output_tail"])
    bundle = home / ".gemini/extensions/lago"
    integrity = verify_bundle(bundle)
    demo = verify_demo(bundle, home, integrity)
    passed = all(s["exit_code"] == 0 for s in steps) and validated and listed and skill["identical"] == 1 and integrity["status"] == "PASS" and demo["passed"]
    return {"agent": "gemini-cli", "cli": GEMINI, "passed": passed, "skill": skill, "steps": steps,
            "integrity": integrity, "offline_demo": demo}


def check_copilot(home: Path) -> dict:
    steps = [
        run(["npx", "-y", COPILOT, "plugin", "marketplace", "add", str(REPO)], home, home),
        run(["npx", "-y", COPILOT, "plugin", "install", "lago@lago-plugins"], home, home),
        run(["npx", "-y", COPILOT, "plugin", "list"], home, home),
    ]
    installed = any("Installed 1 skill" in line for line in steps[1]["output_tail"])
    listed = any("lago@lago-plugins" in line and "enabled" in line for line in steps[2]["output_tail"])
    # A local marketplace is loaded live from the checkout, so the skill file is this checkout's file.
    settings = json.loads((home / ".copilot/settings.json").read_text(encoding="utf-8"))
    source = settings.get("extraKnownMarketplaces", {}).get("lago-plugins", {}).get("source", {})
    source_path = source.get("path")
    source_matches = (source.get("source") == "directory" and isinstance(source_path, str)
                      and Path(source_path).is_absolute() and Path(source_path).resolve() == REPO.resolve())
    enabled = settings.get("enabledPlugins", {}).get("lago@lago-plugins") is True
    skill = installed_skill(home, PLUGIN / "skills")
    integrity = verify_bundle(PLUGIN)
    demo = verify_demo(PLUGIN, home, integrity)
    passed = (all(s["exit_code"] == 0 for s in steps) and installed and listed
              and source_matches and enabled and skill["identical"] == 1
              and integrity["status"] == "PASS" and demo["passed"])
    return {"agent": "github-copilot-cli", "cli": COPILOT, "passed": passed, "steps": steps,
            "source_matches_checkout": source_matches, "enabled_in_settings": enabled,
            "skill": skill, "integrity": integrity, "offline_demo": demo,
            "note": "local marketplace plugins load live from the source directory; nothing is copied"}


def check_skills_sh(home: Path) -> dict:
    project = home / "project"
    project.mkdir()
    initialized = run(["git", "init", "-q"], home, project)
    if initialized["exit_code"] != 0:
        return {"agent": "skills.sh", "passed": False, "steps": [initialized]}
    steps = [run(["npx", "-y", SKILLS, "add", str(REPO), "--skill", "implementation",
                  "-a", "codex", "-a", "cursor", "-a", "github-copilot", "-a", "gemini-cli", "--copy", "-y"], home, project)]
    skill = installed_skill(home, project / ".agents/skills")
    passed = steps[0]["exit_code"] == 0 and skill["identical"] == 1
    return {"agent": "skills.sh", "cli": SKILLS, "passed": passed, "skill": skill, "steps": steps}


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
        "python": sys.version.split()[0],
        "node": subprocess.check_output(["node", "--version"], text=True).strip(),
        "checks": [],
    }
    for check in (check_gemini, check_copilot, check_skills_sh):
        with tempfile.TemporaryDirectory(prefix="lago-agent-install-") as home:
            try:
                report["checks"].append(check(Path(home)))
            except (subprocess.SubprocessError, OSError, ValueError) as error:
                report["checks"].append({"agent": check.__name__, "passed": False, "error": sanitize(str(error), Path(home))})
    end_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    end_dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO, text=True).strip())
    report["source_changed"] = end_commit != report["source_commit"] or end_dirty != dirty
    report["checks_passed"] = all(c["passed"] for c in report["checks"])
    report["complete"] = report["checks_passed"] and not dirty and not report["source_changed"]
    print(json.dumps(report, indent=2))
    return 0 if report["complete"] or (args.allow_dirty and report["checks_passed"]) else 1


if __name__ == "__main__":
    sys.exit(main())
