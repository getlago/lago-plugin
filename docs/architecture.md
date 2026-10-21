# Architecture decision

## Decision

Ship one shared `implementation` skill with eight explicit modes and progressive references. Keep `.claude-plugin` and `.codex-plugin` as thin packaging layers. Bundle only standard-library offline validation scripts, synthetic templates, and evals.

## Why

- One skill preserves a single safety and billing-correctness contract across the lifecycle.
- Mode routing avoids overlapping commands while letting detailed references load only when needed.
- Credential-free offline work keeps installation low-friction and both the Lago CLI and MCP optional.
- Deterministic event, money, reconciliation, demo-target, release-integrity, manifest, link, secret, and public-content checks provide evidence beyond prompt text.

## Boundaries

Application-generated code may call Lago through an official SDK or current REST API. It must not shell out to the Lago CLI. The plugin never contacts Lago on load. For explicit live operator work, an already-installed Lago CLI is an optional execution layer for broad API coverage, structured evidence, and repeatable workflows; connected native tools remain optional alternatives. CLI target verification and commands inherit the same production approval gates as every other live interface. Platform-specific behavior is limited to manifests, marketplace installation, and explicit invocation syntax. Release integrity allows Gemini CLI’s root `.gemini-extension-install.json` as untrusted local installation metadata only when the verified manifest contains `gemini-extension.json`; it does not exempt plugin source, nested files, or symlinks. It likewise allows Claude Code's root `.in_use/<pid>` liveness records, regular files of at most 1 KiB, only when the verified manifest contains `.claude-plugin/plugin.json`. Manifests for other agents (`gemini-extension.json`, `.cursor-plugin/`) are generated from the Claude Code manifests and carry no behavior of their own. GitHub Copilot CLI and Devin read `.claude-plugin/` directly. A `plugin.json` at the repository or plugin root is not allowed, because Copilot CLI and Codex would prefer it over the existing manifests.

The repository is named `lago-plugin`, the shareable marketplace is `lago-plugins`, and the plugin manifest identity is `lago`. This produces the public install target `lago@lago-plugins` and the invocation commands `/lago:implementation` in Claude Code and `$lago:implementation` in Codex. The separate company-only marketplace remains out of the shareable plugin. The public display name is simply “Lago.” In Claude Code terminology, this is a plugin containing an Agent Skill; it is not a custom agent or subagent. At runtime it identifies itself as the Lago Solution Engineer for discovery and becomes the Billing Engineer Copilot when implementation begins.

## Decision: install-free entry point and `@getlago/init` (2026-10-19)

`START_HERE.md` is the entry point for an agent with nothing installed. It carries complete Node.js/TypeScript and Python code for customer sync, subscriptions, idempotent usage events, webhook verification, and entitlement and prepaid-balance checks. Its fenced blocks marked `file=` are the single source of that code. `tests/test_start_here.py` runs them against a local fake Lago API, and `packages/init/templates/` is generated from them with a drift check in CI.

`packages/init` is a second installable surface: a dependency-free Node CLI that detects the stack and copies those templates into an application. It runs code outside the plugin, so it gets these boundaries:

- Dry run by default. `--write` creates files; existing files are never overwritten.
- No network calls, credentials, package installs, or execution of project code. Detection reads manifests only.
- `"private": true` until a maintainer approves publishing under `RELEASING.md`. The name `@getlago/init` was free on npm on 2026-10-19; `create-lago` is taken by an unrelated owner, and the `lago` binary name belongs to the official Go CLI.

## Decision: directory-ready plugin folder (2026-10-20)

The shipped plugin moves from the repository root to `plugins/lago/`, so it can be listed in Anthropic's plugin directory. The directory scans only the submitted plugin folder, and people who install a plugin receive only that folder.

- `plugins/lago/` holds the plugin manifests, the `implementation` skill, `examples/`, the icon, the README with the run/send/store disclosure, a copy of `LICENSE`, and `RELEASE-MANIFEST.json`. The manifest now hashes this folder only.
- Evals, tests, docs, `START_HERE.md`, `packages/init`, and maintainer tooling in `scripts/` stay outside it. They hold synthetic keys, environment-variable examples, and secret-detection patterns that a user never needs and a security scanner could misread.
- The root marketplaces (`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `.cursor-plugin/marketplace.json`) point at `./plugins/lago`, so `lago@lago-plugins` and the Claude Code, Codex, Copilot CLI, and Cursor install commands are unchanged.
- Gemini CLI installs extensions only from a repository root. A GitHub install now uses `gemini skills install --path plugins/lago/skills/implementation`; the full extension installs from a clone with `gemini extensions install ./lago-plugin/plugins/lago`.
- The plugin has no hooks, MCP server, `userConfig`, package launchers, or `!` command lines, so the directory's stricter rules for plugins in a subfolder do not apply. Adding any of them needs a new entry here.

This changes packaging only. No MCP, telemetry, runtime credential, production action, or new skill is added, and the approval gate is unchanged. `scripts/check_directory_limits.py` and ordinary strict manifest validation run in CI. The directory profile runs locally on Claude Code 2.1.305; the older pinned CI version does not support it yet.

## Decision: run-time files only in the plugin folder, optional API URL setting (2026-10-21)

Anthropic's directory validation held the plugin folder for three findings: a script that could reach the bundled icon, a credential presence check, and command-shaped prose. This entry supersedes the `RELEASE-MANIFEST.json` and `userConfig` bullets of the 2026-10-20 entry.

- `release_integrity.py` and `RELEASE-MANIFEST.json` move to `tools/release/`. The manifest still hashes every file in `plugins/lago/`, and CI checks it on every pull request. The skill no longer verifies its own bundle before the demo. A verifier shipped inside the bundle it checks proves no origin, and marketplace installs pin the reviewed commit. The demo guard that remains is the one that matters at run time: run only the plugin's own `run_demo.py`, never a same-named script from the inspected application, and fall back to the reviewed walkthrough if the bundled script is missing or fails. `scripts/validate_repo.py` rejects either file inside the plugin folder.
- The plugin declares one `userConfig` field, `lago_api_url`, non-sensitive, defaulting to Lago Cloud US. Skill content receives it as `${user_config.lago_api_url}`. No API key field is declared. Claude Code never substitutes a sensitive value into skill content and exports `CLAUDE_PLUGIN_OPTION_*` only to hooks, so a declared key could never reach the skill ([manifest reference](https://code.claude.com/docs/en/plugins/manifest-reference)).
- The plugin never reads, tests, or sources a credential from the environment or from files. Live work uses a Lago CLI profile or Lago MCP connection that the user configured. Credential presence is reported by name only, from non-secret sources.
- Codex install steps and the `$lago:implementation` invocation move from the plugin README to the repository README. `.codex-plugin/` and `agents/openai.yaml` stay in the plugin folder, because Codex installs from `./plugins/lago` and reads its manifest there.

No MCP server, hook, telemetry, runtime credential, production action, or new skill is added. The production approval gate is unchanged.
