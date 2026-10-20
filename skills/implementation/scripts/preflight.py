#!/usr/bin/env python3
"""Read-only billing setup inventory for an explicitly selected application repo."""

import argparse
import json
import os
import shutil
from pathlib import Path


SKIP = {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__"}
NON_RUNTIME = {"test", "tests", "__tests__", "evals", "examples", "docs", "scripts"}
SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rb", ".rs", ".java"}
SIGNALS = {
    "customer": ("customer", "account", "tenant", "organization"),
    "subscription": ("subscription", "plan", "enrollment"),
    "usage": ("usage", "event", "meter", "credit", "activity"),
    "billing": ("billing", "invoice", "payment", "stripe", "chargebee"),
}
AGENTS = {"claude_code": "claude", "codex": "codex", "copilot_cli": "copilot", "gemini_cli": "gemini"}
INSTALL = {
    "claude_code": ["/plugin marketplace add getlago/lago-plugin", "/plugin install lago@lago-plugins", "/lago:implementation map billing in this application"],
    "codex": ["codex plugin marketplace add getlago/lago-plugin", "codex plugin add lago@lago-plugins", "$lago:implementation map billing in this application"],
    "copilot_cli": ["copilot plugin marketplace add getlago/lago-plugin", "copilot plugin install lago@lago-plugins"],
    "gemini_cli": ["gemini extensions install https://github.com/getlago/lago-plugin"],
}


def inspect(root):
    if not root.is_dir():
        raise ValueError("Open an application repository directory")
    files = []
    for folder, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP and not d.startswith("."))
        for name in sorted(names):
            path = Path(folder) / name
            if path.is_symlink() or name.startswith("."):
                continue
            rel = path.relative_to(root)
            if len(rel.parts) <= 6:
                files.append(rel.as_posix())
            if len(files) >= 3000:
                break
        if len(files) >= 3000:
            break
    manifest = [name for name in ("package.json", "pyproject.toml", "requirements.txt", "go.mod", "Cargo.toml") if name in files]
    signals = {kind: [] for kind in SIGNALS}
    for name in files:
        path = root / name
        if any(part in NON_RUNTIME for part in Path(name).parts[:-1]):
            continue
        if path.suffix not in SOURCE_SUFFIXES or path.stat().st_size > 1_000_000:
            continue
        try:
            source = path.read_text(encoding="utf-8").lower()
        except (OSError, UnicodeError):
            continue
        for kind, words in SIGNALS.items():
            if len(signals[kind]) < 12 and any(word in source for word in words):
                signals[kind].append(name)
    available_agents = [name for name, command in AGENTS.items() if shutil.which(command)]
    return {
        "repository": str(root),
        "git_repository": (root / ".git").exists(),
        "application_manifests": manifest,
        "candidate_source_files": signals,
        "available_agent_commands": available_agents,
        "install_guidance_for_available_agents": {name: INSTALL[name] for name in available_agents},
        "lago_cli_installed": bool(shutil.which("lago")),
        "lago_api_key_present": "LAGO_API_KEY" in os.environ,
        "lago_api_url_present": "LAGO_API_URL" in os.environ,
        "target_organization_verified": False,
        "live_actions_taken": False,
        "next": [
            "Open the application in your coding agent and invoke Lago's implementation skill.",
            "Confirm payer, price, current invoice/payment owner, metric, plan, customer, subscription, and event IDs from code before live writes.",
            "When authorized to contact the exact target, run lago whoami and lago doctor; compare the organization and API host with the intended target.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", nargs="?", default=".")
    args = parser.parse_args()
    print(json.dumps(inspect(Path(args.repository).resolve()), indent=2))


if __name__ == "__main__":
    main()
