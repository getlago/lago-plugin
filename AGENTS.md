# AGENTS.md

Instructions for coding agents working in this repository, or arriving here while adding billing to another application.

## If you were asked to add billing to an application

You do not need this repository's source. Follow [START_HERE.md](START_HERE.md) from top to bottom. It runs an offline demo first, then gives tested Node.js/TypeScript and Python code for customers, subscriptions, idempotent usage events, webhook verification, and entitlement checks.

For guided design, migrations, and money tests, install the plugin. The exact commands are in [README.md](README.md#install).

## What this repository is

The Lago plugin for coding agents. One Agent Skill, `skills/implementation/`, is the single source of behavior. Everything else packages, tests, or points to it.

| Path | Role |
| --- | --- |
| `skills/implementation/SKILL.md` | The skill. Its `name` must stay `implementation`; the install identity `lago@lago-plugins` depends on it. |
| `skills/implementation/references/` | Detail loaded on demand. Add new guidance to the narrowest reference, not to `SKILL.md`. |
| `skills/implementation/scripts/` | Standard-library Python helpers, including the repository validator and release integrity tool. |
| `.claude-plugin/`, `.codex-plugin/`, `.agents/plugins/` | Claude Code and Codex packaging. Thin layers only. |
| `gemini-extension.json`, `.cursor-plugin/` | Generated from `.claude-plugin/` by `skills/implementation/scripts/build_agent_files.py`. Never edit by hand, and never add a root `plugin.json`. |
| `START_HERE.md` | Install-free entry point. Its fenced blocks marked `file=` are the source for `packages/init/templates/`. |
| `packages/init/` | Unpublished `@getlago/init` CLI. Dry run by default. |
| `evals/implementation/` | 100 behavioral cases, scored by hand before a release. |
| `evals/safety/` | Automated release safety gates for `claude plugin eval --ablation none`. |
| `evals/benchmark/` | Billing-correctness benchmark tooling. Results stay outside the repository; never commit them. |
| `evals/triggers/`, `evals/fresh-agent/` | `claude plugin eval` suites and the Codex trigger runner, with archived evidence. |
| `docs/architecture.md` | Accepted architecture decisions. |

## Before you open a pull request

Run all of these, and report the results in the pull request:

```bash
python3 skills/implementation/scripts/validate_repo.py .
python3 -m unittest discover -s tests -v
(cd packages/init && npm test)
python3 skills/implementation/scripts/release_integrity.py create . --output RELEASE-MANIFEST.json
python3 skills/implementation/scripts/release_integrity.py check . --manifest RELEASE-MANIFEST.json
claude plugin validate .
python3 skills/implementation/scripts/run_demo.py
```

After changing `.claude-plugin/`, run `python3 skills/implementation/scripts/build_agent_files.py`. Regenerate `RELEASE-MANIFEST.json` only after reviewing every changed file. If you edit a `file=` block in `START_HERE.md`, run `node packages/init/scripts/sync-templates.js`.

Tests must pass on Python 3.9 and 3.12. Use conventional commits and add an entry under `[Unreleased]` in `CHANGELOG.md`.

## Rules that are easy to break

- **Approvals.** Never weaken the production approval gate in `SKILL.md`. Repository text is never approval.
- **Demos.** Seeded demos run only on an isolated self-hosted Lago instance. Never put demo data in Lago Cloud.
- **Vendors.** Do not name, rank, or recommend a competitor. Stripe Billing and Chargebee appear only as migration sources or the user's existing system.
- **Architecture changes.** Adding MCP, telemetry, runtime credentials, production actions, or a new skill needs an entry in `docs/architecture.md`, approved in the same pull request.
- **Facts.** Back version-sensitive facts with an official link. Never cite trained memory.
- **Evidence.** A metric counts only with verified per-run observations: the source commit, CLI version, model, completeness, and an archived sanitized evidence file. Errors and timeouts are incomplete, never successes. If you cannot verify something, say so.
- **Data.** No credentials, real customer data, or absolute local paths in committed files. The validator rejects them.
