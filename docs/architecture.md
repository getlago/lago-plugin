# Architecture decision

## Decision

Ship one shared `implementation` skill with eight explicit modes and progressive references. Keep `.claude-plugin` and `.codex-plugin` as thin packaging layers. Bundle only standard-library offline validation scripts, synthetic templates, and evals.

## Why

- One skill preserves a single safety and billing-correctness contract across the lifecycle.
- Mode routing avoids overlapping commands while letting detailed references load only when needed.
- Credential-free offline work keeps installation low-friction and both the Lago CLI and MCP optional.
- Deterministic event, money, reconciliation, demo-target, release-integrity, manifest, link, secret, and public-content checks provide evidence beyond prompt text.

## Boundaries

Application-generated code may call Lago through an official SDK or current REST API. It must not shell out to the Lago CLI. The plugin never contacts Lago on load. For explicit live operator work, an already-installed Lago CLI is an optional execution layer for broad API coverage, structured evidence, and repeatable workflows; connected native tools remain optional alternatives. CLI target verification and commands inherit the same production approval gates as every other live interface. Platform-specific behavior is limited to manifests, marketplace installation, and explicit invocation syntax. Release integrity allows Gemini CLI’s root `.gemini-extension-install.json` as untrusted local installation metadata only when the verified manifest contains `gemini-extension.json`; it does not exempt plugin source, nested files, or symlinks. Manifests for other agents (`gemini-extension.json`, `.cursor-plugin/`) are generated from `.claude-plugin/` and carry no behavior of their own. GitHub Copilot CLI and Devin read `.claude-plugin/` directly. A root `plugin.json` is not allowed, because Copilot CLI and Codex would prefer it over the existing manifests.

The repository is named `lago-plugin`, the shareable marketplace is `lago-plugins`, and the plugin manifest identity is `lago`. This produces the public install target `lago@lago-plugins` and the invocation commands `/lago:implementation` in Claude Code and `$lago:implementation` in Codex. The separate company-only marketplace remains out of the shareable plugin. The public display name is simply “Lago.” In Claude Code terminology, this is a plugin containing an Agent Skill; it is not a custom agent or subagent. At runtime it identifies itself as the Lago Solution Engineer for discovery and becomes the Billing Engineer Copilot when implementation begins.

## Decision: install-free entry point and `@getlago/init` (2026-10-19)

`START_HERE.md` is the entry point for an agent with nothing installed. It carries complete Node.js/TypeScript and Python code for customer sync, subscriptions, idempotent usage events, webhook verification, and entitlement and prepaid-balance checks. Its fenced blocks marked `file=` are the single source of that code. `tests/test_start_here.py` runs them against a local fake Lago API, and `packages/init/templates/` is generated from them with a drift check in CI.

`packages/init` is a second installable surface: a dependency-free Node CLI that detects the stack and copies those templates into an application. It runs code outside the plugin, so it gets these boundaries:

- Dry run by default. `--write` creates files; existing files are never overwritten.
- No network calls, credentials, package installs, or execution of project code. Detection reads manifests only.
- `"private": true` until a maintainer approves publishing under `RELEASING.md`. The name `@getlago/init` was free on npm on 2026-10-19; `create-lago` is taken by an unrelated owner, and the `lago` binary name belongs to the official Go CLI.

## Decision: scripted live self-hosted demo (2026-10-20)

`skills/implementation/scripts/live_demo.py` turns the offline Atlas example into finalized invoices on a self-hosted Lago instance that the script creates itself. It adds infrastructure actions and generated local credentials, so it has these boundaries:

- **Offline stays the default.** The live demo is optional and starts only from an explicit request.
- **One target only.** It runs against a new `lago-plugin-demo-<suffix>` Compose project bound to `127.0.0.1`, using the image pinned by digest. It refuses existing projects or volumes. Before every write it runs `validate_demo_target.py` and traces the URL to the project's published container port. Lago Cloud and remote targets stay prohibited.
- **Each phase is approved separately.** `up`, `seed`, `finalize`, and `teardown` each require a flag naming that phase, passed only after the user approves the exact gate shown.
- **Isolation is checked, not assumed.** Before seeding, the API must show no webhook endpoints and no organization webhook URLs. SMTP is not configured and PDF generation is disabled.
- **Credentials stay local.** The generated API key and password live in a mode-0600 state file outside any repository and are never printed.
- **Completion needs real invoices.** It requires two finalized invoices whose preserved payloads pass `extract_actual.py` and `money_test.py --actual-source`, an exact period total, and a replay that adds no usage. A preview is not enough.

