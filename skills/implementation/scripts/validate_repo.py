#!/usr/bin/env python3
"""Deterministic public-plugin checks; standard library only."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py", ".txt", ".csv"}
SECRET_PATTERNS = {
    "Lago API key": re.compile(r"\blago_[A-Za-z0-9]{24,}\b", re.I),
    "Stripe live key": re.compile(r"\b(?:sk|rk)_live_[A-Za-z0-9]{16,}\b"),
    "Lago key assignment": re.compile(r"LAGO_[A-Z_]*KEY\s*[=:]\s*['\"][A-Za-z0-9-]{20,}['\"]", re.I),
    "Chargebee key assignment": re.compile(r"CHARGEBEE_[A-Z_]*KEY\s*=\s*['\"][^_\s][^'\"]{12,}['\"]", re.I),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
PRIVATE_URL = re.compile(r"https?://(?:[^/]*\.)?(?:notion\.so|hubspot\.com|slack\.com|drive\.google\.com)/", re.I)
ABSOLUTE_PATH = re.compile(r"(?<!https:)(?<!http:)\B/(?:Users|home|private|var|tmp)/[^\s)`'\"]+")
MARKER = re.compile(r"\[(?:TODO|FIXME)(?::[^\]]*)?\]", re.I)
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def load_json(path: Path, failures: list[str]) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:  # deterministic report, not a traceback
        failures.append(f"invalid JSON: {path}: {error}")
        return {}


def iter_text(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES and ".git" not in path.parts:
            yield path, path.read_text(encoding="utf-8")


def validate(root: Path, denylist: Path | None) -> list[str]:
    failures: list[str] = []
    codex = root / ".codex-plugin/plugin.json"
    claude = root / ".claude-plugin/plugin.json"
    codex_marketplace = root / ".agents/plugins/marketplace.json"
    claude_marketplace = root / ".claude-plugin/marketplace.json"
    skill = root / "skills/implementation/SKILL.md"
    primitives = root / "skills/implementation/references/primitives.md"
    demo = root / "skills/implementation/references/demo.md"
    validation = root / "skills/implementation/references/validation.md"
    openai_yaml = root / "skills/implementation/agents/openai.yaml"
    required_scripts = (
        root / "skills/implementation/scripts/extract_actual.py",
        root / "skills/implementation/scripts/list_external_links.py",
        root / "skills/implementation/scripts/money_test.py",
        root / "skills/implementation/scripts/reconcile.py",
        root / "skills/implementation/scripts/run_demo.py",
        root / "skills/implementation/scripts/validate_event.py",
        root / "skills/implementation/scripts/validate_repo.py",
    )
    for required in (codex, claude, codex_marketplace, claude_marketplace, skill, primitives, demo, validation, openai_yaml, *required_scripts, root / "README.md", root / "LICENSE"):
        if not required.is_file():
            failures.append(f"missing required file: {required.relative_to(root)}")
    codex_data, claude_data = load_json(codex, failures), load_json(claude, failures)
    for label, data in (("Codex", codex_data), ("Claude", claude_data)):
        if isinstance(data, dict):
            if data.get("name") != "lago":
                failures.append(f"{label} manifest name must be lago")
            if data.get("version") != "0.1.0":
                failures.append(f"{label} manifest version must match release")
    for label, path in (("Codex", codex_marketplace), ("Claude", claude_marketplace)):
        marketplace = load_json(path, failures)
        if not isinstance(marketplace, dict) or marketplace.get("name") != "getlago":
            failures.append(f"{label} marketplace name must be getlago")
            continue
        plugins = marketplace.get("plugins")
        if not isinstance(plugins, list) or not any(
            isinstance(plugin, dict) and plugin.get("name") == "lago"
            for plugin in plugins
        ):
            failures.append(f"{label} marketplace must expose lago@getlago")
    if isinstance(codex_data, dict):
        interface = codex_data.get("interface")
        prompts = interface.get("defaultPrompt", []) if isinstance(interface, dict) else []
        if not isinstance(prompts, list) or not prompts or any(
            not isinstance(prompt, str) or len(prompt) > 128 for prompt in prompts
        ):
            failures.append("Codex interface.defaultPrompt entries must be non-empty and at most 128 characters")
    if skill.is_file():
        text = skill.read_text(encoding="utf-8")
        if not re.match(r"^---\nname: implementation\ndescription: .+\n---\n", text):
            failures.append("skill frontmatter is invalid")
        for mode in ("assess", "design", "implement", "deploy", "migrate", "validate", "reconcile", "troubleshoot"):
            if f"`{mode}`" not in text:
                failures.append(f"skill does not route mode: {mode}")
        for preflight_signal in ("Lago Billing Engineer loaded.", "Mandatory first-run preflight", "credentials are unnecessary for offline work", "Ask only the next question"):
            if preflight_signal not in text:
                failures.append(f"missing first-run behavior: {preflight_signal}")
        if "never answer a version-sensitive question from trained memory" not in text:
            failures.append("missing official-documentation freshness guard")
    if primitives.is_file():
        text = primitives.read_text(encoding="utf-8")
        for teaching_signal in ("Your application → Lago", "Never quiz the user", "Billable metric", "Payment collection is a separate integration decision"):
            if teaching_signal not in text:
                failures.append(f"missing beginner primitive guidance: {teaching_signal}")
    if demo.is_file():
        text = demo.read_text(encoding="utf-8")
        for demo_signal in ("Lago has no built-in sandbox mode", "Never seed demo customers", "including an account the user calls development, test, or staging", "isolated self-hosted Lago instance"):
            if demo_signal not in text:
                failures.append(f"missing demo isolation guidance: {demo_signal}")
    if validation.is_file():
        text = validation.read_text(encoding="utf-8")
        for evidence_signal in ("extract_actual.py", "Never hand-write", "--actual-source"):
            if evidence_signal not in text:
                failures.append(f"missing money-evidence guidance: {evidence_signal}")
    if openai_yaml.is_file() and "$lago:implementation" not in openai_yaml.read_text(encoding="utf-8"):
        failures.append("Codex default prompt must use the installed namespaced skill invocation")
    denied = []
    if denylist:
        denied = [line.strip().lower() for line in denylist.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
    for path, text in iter_text(root):
        rel = path.relative_to(root)
        if MARKER.search(text):
            failures.append(f"unfinished marker: {rel}")
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                failures.append(f"possible {name}: {rel}")
        if path.name != "validate_repo.py" and PRIVATE_URL.search(text):
            failures.append(f"private/workspace URL: {rel}")
        if path.name != "validate_repo.py" and ABSOLUTE_PATH.search(text):
            failures.append(f"unsupported absolute path: {rel}")
        lowered = text.lower()
        for term in denied:
            if term in lowered:
                failures.append(f"denylisted public content '{term}': {rel}")
        if path.suffix.lower() == ".md":
            for target in MARKDOWN_LINK.findall(text):
                target = target.split("#", 1)[0]
                if not target or re.match(r"(?:https?|mailto):", target):
                    continue
                resolved = (path.parent / target).resolve()
                try:
                    resolved.relative_to(root.resolve())
                except ValueError:
                    failures.append(f"link escapes repository: {rel} -> {target}")
                    continue
                if not resolved.exists():
                    failures.append(f"broken relative link: {rel} -> {target}")
    main = skill.read_text(encoding="utf-8") if skill.is_file() else ""
    for gate in ("target environment", "affected objects", "billing impact", "rollback/recovery", "explicit approval"):
        if gate not in main.lower():
            failures.append(f"missing production approval gate: {gate}")
    return sorted(set(failures))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--denylist", type=Path, help="optional private list of names/terms; one per line")
    args = parser.parse_args()
    failures = validate(args.root.resolve(), args.denylist)
    print(json.dumps({"status": "PASS" if not failures else "FAIL", "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
