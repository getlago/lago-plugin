#!/usr/bin/env python3
"""Generate per-agent manifests from the Claude Code manifests; standard library only.

`plugins/lago/.claude-plugin/plugin.json` and the root `.claude-plugin/marketplace.json`
are the single source of name, version, and description. Agents that already read `.claude-plugin/`
(GitHub Copilot CLI, Devin) or `skills/*/SKILL.md` directly (skills.sh, gh skill,
Amp) need no generated file. Formats, checked against raw docs on 2026-10-19:

- Gemini CLI extension, also read by Goose: `gemini-extension.json` at the extension
  root (here the plugin folder), `name` and `version` required, skills discovered in
  `skills/*/SKILL.md`.
  https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/extensions/reference.md
- Cursor plugin and marketplace: `.cursor-plugin/plugin.json` (only `name` required,
  `skills` path) and `.cursor-plugin/marketplace.json` (`name`, `owner.name`,
  `plugins[].name`, `plugins[].source`). https://cursor.com/docs/reference/plugins.md

- Copilot CLI compatibility and manifest lookup:
  https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference
- Goose Gemini extension compatibility:
  https://raw.githubusercontent.com/aaif-goose/goose/main/documentation/docs/guides/context-engineering/plugins.md
- Devin Claude manifest compatibility:
  https://docs.devin.ai/cli/extensibility/plugins

Never generate a `plugin.json` at the repository or plugin root: Copilot CLI prefers it over `.claude-plugin/`,
and Codex reads it before `.codex-plugin/plugin.json`.

Usage: build_agent_files.py [root] [--check]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def render(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


PLUGIN = "plugins/lago"


def generated(root: Path) -> dict[str, str]:
    plugin = json.loads((root / PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    marketplace = json.loads((root / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    entry = next(p for p in marketplace["plugins"] if p["name"] == plugin["name"])
    return {
        f"{PLUGIN}/gemini-extension.json": render({
            "name": plugin["name"],
            "version": plugin["version"],
            "description": plugin["description"],
        }),
        f"{PLUGIN}/.cursor-plugin/plugin.json": render({
            "name": plugin["name"],
            "version": plugin["version"],
            "description": plugin["description"],
            "skills": plugin["skills"],
        }),
        ".cursor-plugin/marketplace.json": render({
            "name": marketplace["name"],
            "owner": marketplace["owner"],
            "plugins": [{"name": entry["name"], "source": entry["source"], "description": entry["description"]}],
        }),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true", help="exit 1 if any generated file differs")
    args = parser.parse_args()
    root = args.root.resolve()
    drift = []
    for relative, content in generated(root).items():
        target = root / relative
        current = target.read_text(encoding="utf-8") if target.is_file() else None
        if current == content:
            continue
        if args.check:
            drift.append(relative)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
    print(json.dumps({"status": "FAIL" if drift else "PASS", "drift": drift}, indent=2))
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
