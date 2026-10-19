# Architecture decision

## Decision

Ship one shared `implementation` skill with eight explicit modes and progressive references. Keep `.claude-plugin` and `.codex-plugin` as thin packaging layers. Bundle only standard-library offline validation scripts, synthetic templates, and evals.

## Why

- One skill preserves a single safety and billing-correctness contract across the lifecycle.
- Mode routing avoids overlapping commands while letting detailed references load only when needed.
- Credential-free offline work keeps installation low-friction and both the Lago CLI and MCP optional.
- Deterministic event, money, reconciliation, demo-target, release-integrity, manifest, link, secret, and public-content checks provide evidence beyond prompt text.

## Boundaries

Application-generated code may call Lago through an official SDK or current REST API. It must not shell out to the Lago CLI. The plugin never contacts Lago on load. For explicit live operator work, an already-installed Lago CLI is an optional execution layer for broad API coverage, structured evidence, and repeatable workflows; connected native tools remain optional alternatives. CLI target verification and commands inherit the same production approval gates as every other live interface. Platform-specific behavior is limited to manifests, marketplace installation, and explicit invocation syntax.

The repository is named `lago-plugin`, the shareable marketplace is `lago-plugins`, and the plugin manifest identity is `lago`. This produces the public install target `lago@lago-plugins` and the invocation commands `/lago:implementation` in Claude Code and `$lago:implementation` in Codex. The separate company-only marketplace remains out of the shareable plugin. The public display name is simply “Lago.” In Claude Code terminology, this is a plugin containing an Agent Skill; it is not a custom agent or subagent. At runtime it identifies itself as the Lago Solution Engineer for discovery and becomes the Billing Engineer Copilot when implementation begins.

## Decision: install-free entry point and `@getlago/init` (2026-10-19)

`START_HERE.md` is the entry point for an agent with nothing installed. It carries complete Node.js/TypeScript and Python code for customer sync, subscriptions, idempotent usage events, webhook verification, and entitlement and prepaid-balance checks. Its fenced blocks marked `file=` are the single source of that code. `tests/test_start_here.py` runs them against a local fake Lago API, and `packages/init/templates/` is generated from them with a drift check in CI.

`packages/init` is a second installable surface: a dependency-free Node CLI that detects the stack and copies those templates into an application. It runs code outside the plugin, so it gets these boundaries:

- Dry run by default. `--write` creates files; existing files are never overwritten.
- No network calls, credentials, package installs, or execution of project code. Detection reads manifests only.
- `"private": true` until a maintainer approves publishing under `RELEASING.md`. The name `@getlago/init` was free on npm on 2026-10-19; `create-lago` is taken by an unrelated owner, and the `lago` binary name belongs to the official Go CLI.
