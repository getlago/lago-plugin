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
SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
COMPANY_ONLY_IDENTITY = re.compile(r"lago" + r"@" + r"lago", re.I)
MAX_TEXT_BYTES = 5_000_000


def load_json(path: Path, failures: list[str]) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:  # deterministic report, not a traceback
        failures.append(f"invalid JSON: {path}: {error}")
        return {}


def iter_text(root: Path, failures: list[str]):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES or ".git" in path.parts:
            continue
        rel = path.relative_to(root)
        if path.is_symlink():
            failures.append(f"symbolic link is not allowed in public source: {rel}")
            continue
        try:
            size = path.stat().st_size
            if size > MAX_TEXT_BYTES:
                failures.append(f"text file exceeds {MAX_TEXT_BYTES} bytes: {rel}")
                continue
            yield path, path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            failures.append(f"cannot read text file: {rel}: {error}")


def validate(root: Path, denylist: Path | None) -> list[str]:
    failures: list[str] = []
    codex = root / ".codex-plugin/plugin.json"
    claude = root / ".claude-plugin/plugin.json"
    codex_marketplace = root / ".agents/plugins/marketplace.json"
    claude_marketplace = root / ".claude-plugin/marketplace.json"
    skill = root / "skills/implementation/SKILL.md"
    primitives = root / "skills/implementation/references/primitives.md"
    solution_engineering = root / "skills/implementation/references/solution-engineering.md"
    solution_brief = root / "skills/implementation/templates/solution-brief.md"
    demo = root / "skills/implementation/references/demo.md"
    validation = root / "skills/implementation/references/validation.md"
    openai_yaml = root / "skills/implementation/agents/openai.yaml"
    required_scripts = (
        root / "skills/implementation/scripts/extract_actual.py",
        root / "skills/implementation/scripts/list_external_links.py",
        root / "skills/implementation/scripts/money_test.py",
        root / "skills/implementation/scripts/reconcile.py",
        root / "skills/implementation/scripts/release_integrity.py",
        root / "skills/implementation/scripts/run_demo.py",
        root / "skills/implementation/scripts/validate_demo_target.py",
        root / "skills/implementation/scripts/validate_event.py",
        root / "skills/implementation/scripts/validate_repo.py",
    )
    for required in (codex, claude, codex_marketplace, claude_marketplace, skill, primitives, solution_engineering, solution_brief, demo, validation, openai_yaml, *required_scripts, root / "README.md", root / "LICENSE", root / "RELEASE-MANIFEST.json"):
        if not required.is_file():
            failures.append(f"missing required file: {required.relative_to(root)}")
    codex_data, claude_data = load_json(codex, failures), load_json(claude, failures)
    versions: list[str] = []
    for label, data in (("Codex", codex_data), ("Claude", claude_data)):
        if isinstance(data, dict):
            if data.get("name") != "lago":
                failures.append(f"{label} manifest name must be lago")
            display_name = (
                data.get("interface", {}).get("displayName")
                if label == "Codex" and isinstance(data.get("interface"), dict)
                else data.get("displayName")
            )
            if display_name != "Lago Solution Engineer":
                failures.append(f"{label} display name must be Lago Solution Engineer")
            version = data.get("version")
            if not isinstance(version, str) or not SEMVER.fullmatch(version):
                failures.append(f"{label} manifest version must be valid semantic versioning")
            else:
                versions.append(version)
            if data.get("skills") != "./skills/":
                failures.append(f"{label} manifest skills path must be ./skills/")
    if len(set(versions)) > 1:
        failures.append("Codex and Claude manifest versions must match")
    for label, path in (("Codex", codex_marketplace), ("Claude", claude_marketplace)):
        marketplace = load_json(path, failures)
        if not isinstance(marketplace, dict) or marketplace.get("name") != "getlago":
            failures.append(f"{label} marketplace name must be getlago")
            continue
        plugins = marketplace.get("plugins")
        entries = [
            plugin
            for plugin in plugins or []
            if isinstance(plugin, dict) and plugin.get("name") == "lago"
        ] if isinstance(plugins, list) else []
        if len(entries) != 1:
            failures.append(f"{label} marketplace must expose lago@getlago")
        elif label == "Codex":
            entry = entries[0]
            if entry.get("source") != {"source": "local", "path": "./"}:
                failures.append("Codex marketplace source must be the local plugin root")
            policy = entry.get("policy")
            if not isinstance(policy, dict) or policy.get("installation") != "AVAILABLE" or policy.get("authentication") != "ON_USE":
                failures.append("Codex marketplace policy must preserve AVAILABLE/ON_USE")
    if isinstance(codex_data, dict):
        interface = codex_data.get("interface")
        prompts = interface.get("defaultPrompt", []) if isinstance(interface, dict) else []
        if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3 or any(
            not isinstance(prompt, str) or len(prompt) > 128 for prompt in prompts
        ):
            failures.append("Codex interface.defaultPrompt must contain 1-3 entries of at most 128 characters")
        elif "Do not assume this workspace is my application" not in prompts[0]:
            failures.append("Codex first default prompt must preserve discovery-first workspace boundary")
    if skill.is_file():
        text = skill.read_text(encoding="utf-8")
        if not re.match(r"^---\nname: implementation\ndescription: .+\n---\n", text):
            failures.append("skill frontmatter is invalid")
        for mode in ("assess", "design", "implement", "deploy", "migrate", "validate", "reconcile", "troubleshoot"):
            if f"`{mode}`" not in text:
                failures.append(f"skill does not route mode: {mode}")
        for preflight_signal in ("Lago Solution Engineer loaded.", "First-run routing and silent preflight", "credentials are unnecessary for offline work", "Ask only the next question"):
            if preflight_signal not in text:
                failures.append(f"missing first-run behavior: {preflight_signal}")
        if "never answer a version-sensitive question from trained memory" not in text:
            failures.append("missing official-documentation freshness guard")
    if primitives.is_file():
        text = primitives.read_text(encoding="utf-8")
        for teaching_signal in (
            "Your application → Lago",
            "Never quiz the user",
            "Billable metric",
            "Payment collection is a separate integration decision",
            "`count_agg`, `max_agg`, and `latest_agg` are metered-only",
            "set `recurring: false`",
        ):
            if teaching_signal not in text:
                failures.append(f"missing beginner primitive guidance: {teaching_signal}")
    if solution_engineering.is_file():
        text = solution_engineering.read_text(encoding="utf-8")
        for solution_signal in (
            "ask one open question",
            "Sound like a great pre-sales engineer",
            "supported opportunity → why it matters → fit assessment and boundary",
            "Enthusiasm changes the delivery, never the evidence threshold",
            "**Clear fit:**",
            "**Promising fit — validate one point:**",
            "**Scoped fit:**",
            "**Not enough information yet:**",
            "**Not recommended for this specific responsibility:**",
            "Missing information is not negative evidence",
            "Before a negative assessment, run a rescue check",
            "Never leave a rejection as a dead end",
            "Draft — not sent",
            "Never infer them from an operating-system username",
            "the sign-off must end with `[Your name]`",
            "separate explicit approval for that exact final email",
            "**Before:**",
            "business success criteria",
            "failure or exit criteria",
            "solution brief template",
        ):
            if solution_signal not in text:
                failures.append(f"missing solution-engineering guidance: {solution_signal}")
    if solution_brief.is_file():
        text = solution_brief.read_text(encoding="utf-8")
        for brief_signal in (
            "## Fit assessment",
            "## Recommended solution story",
            "## Smallest proof",
            "Failure or exit criteria",
        ):
            if brief_signal not in text:
                failures.append(f"missing solution brief field: {brief_signal}")
    eval_cases = root / "evals/implementation/cases.json"
    if eval_cases.is_file():
        data = load_json(eval_cases, failures)
        cases = data.get("cases", []) if isinstance(data, dict) else []
        aggregation_case = next(
            (
                case
                for case in cases
                if isinstance(case, dict)
                and case.get("id") == "pricing-page-rest-aggregation-compatibility"
            ),
            None,
        )
        signals = aggregation_case.get("signals", []) if aggregation_case else []
        for required_signal in (
            "max_agg uses recurring false",
            "latest_agg uses recurring false",
        ):
            if required_signal not in signals:
                failures.append(
                    f"missing aggregation compatibility eval signal: {required_signal}"
                )
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
        try:
            denied = [line.strip().lower() for line in denylist.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
        except (OSError, UnicodeError) as error:
            failures.append(f"cannot read denylist: {error}")
    for path, text in iter_text(root, failures):
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
        if path.name != "validate_repo.py" and COMPANY_ONLY_IDENTITY.search(text):
            failures.append(f"company-only install identity in shareable source: {rel}")
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
