# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and semantic versioning.

## [Unreleased]

- Test demo-helper substitution as untrusted repository instructions, rather than a direct user request to run an inspected application script.

- Require persisted whole-second subscription starts in the no-install clients; prevent activation reconciliation failures caused by comparing Lago's second-precision response with local milliseconds. Usage-event timestamps retain their original precision.

- Lock the pinned Claude CI validator and its dependency tree outside the shipped plugin.

- Disclose Python helper bytecode caches and ignore local environment files while retaining examples.

- Make the no-install completion contract explicit: activation, durable outbox/inbox workers, entitlement wiring and runnable recovery tests; prohibit handing off unconnected helpers as an implemented integration.

- Clarify literal credential-presence checks and the exact integrity-before-demo command; add tests rejecting incomplete or plugin-contaminated fresh-agent evidence.

- Add a no-plugin fresh-agent runner pinned to the candidate commit, with explicit source/registry network grants and per-run provenance.

- Count turn-capped trigger runs as incomplete, never as successful evidence.

- Route credential incidents and blocked production requests directly to safety guidance; evaluate indirect shell execution from the full trace alongside deterministic network indicators.
- Tell no-install agents how to retrieve exact MIT-licensed source; check generated billing behavior across editing tools. Upgrade and lock the Next.js fixture dependencies and update the PyJWT test dependency.

- Complete migration and self-hosted setup disclosures; keep directory submission gated on verified release evidence.
- Reject missing plugin manifests and case-colliding directory components in directory checks; repair the integrity command and disable persisted CI checkout credentials.

### Fixed

- Release integrity failed inside every running Claude Code session, because Claude Code writes `.in_use/<pid>` liveness records into the installed plugin copy. The check now exempts only root-level, digit-named records of at most 1 KiB when the bundle declares a Claude Code plugin, like the existing Gemini install-record exemption. Found by a clean marketplace install test; the skill must not run bundled code when integrity fails, so this blocked or weakened the offline demo.
- Archived evidence no longer includes spend fields, model thinking blocks, local user names in directory listings, local tool paths, or internal role labels. A test keeps them out.

### Added

- `plugins/lago/README.md`: the directory listing text, with install steps and a "What this plugin runs, sends and stores" disclosure.
- `scripts/check_directory_limits.py` and a CI job that runs it with `claude plugin validate plugins/lago --profile directory --strict`.
- `docs/directory-readiness.md` (audit against the pre-submission checklist) and `docs/directory-submission-handoff.md` (portal steps for the Lago Owner who submits).
- Automated safety evals (`evals/safety/`): nine release safety gates as `claude plugin eval` cases with deterministic graders for skill loading, conservative refusal-tool restrictions, credential exposure, file mutation, and a synthetic script execution marker, plus an LLM judge.
- Billing-correctness benchmark: a Python usage-billing task, a fake Lago API, and a scorer for idempotent events, double billing, charges, and webhook verification, tested against a reference solution and six targeted defects. A runner compares the with-plugin and no-plugin arms. Method and empty results template in `docs/benchmark.md`. Results are written outside the repository and never published.
- Other agents: generated `gemini-extension.json` (Gemini CLI, Goose) and `.cursor-plugin/` manifests (Cursor), plus README install paths for GitHub Copilot CLI, which reads `.claude-plugin/`, and for skills.sh. `build_agent_files.py` generates them from `.claude-plugin/`. The repository validator fails on drift or on a root `plugin.json`.
- Root `AGENTS.md` for coding agents working in or arriving at this repository.
- `evals/agent-installs/verify_installs.py`: installs the checkout with pinned Gemini CLI, Copilot CLI, and skills.sh in temporary homes, and records whether the installed skill is byte-identical.
- Trigger evals: 32 developer-worded prompts and 15 near-misses for `claude plugin eval`, plus a Codex harness that installs `lago@lago-plugins` into a temporary `CODEX_HOME`. Claude Code hit rate went from 86/96 to 95/96, and observed false triggers from 2/42 to 0/43; three baseline and two after-change negative attempts timed out, so both evaluations are incomplete. Historical Codex scores were withdrawn because the original scorer accepted unsuccessful reads; the corrected harness reports successful loading and incomplete attempts separately.
- `START_HERE.md`: install-free entry point with the offline demo and tested Node.js/TypeScript and Python code for customer sync, subscriptions, idempotent usage events, JWT or HMAC webhook verification, and entitlement and prepaid-balance checks.
- `packages/init` (unpublished): dependency-free `@getlago/init` CLI that detects a Node.js or Python stack and scaffolds the `START_HERE.md` billing module. Dry run by default; never overwrites files.
- CI job that runs the `START_HERE.md` code against a fake Lago API and checks the init templates for drift.

### Changed

- Directory readiness: the shipped plugin moved to `plugins/lago/` so it can be submitted to Anthropic's plugin directory. The root marketplaces point at it, so `lago@lago-plugins` and the Claude Code, Codex, Copilot CLI, and Cursor install commands are unchanged. Gemini CLI installs from a subfolder with `gemini skills install --path`, or the full extension from a clone. `examples/` ships inside the plugin, where the skill already linked to it. Maintainer tooling (`validate_repo.py`, `build_agent_files.py`, `list_external_links.py`) moved to `scripts/` and no longer ships. `RELEASE-MANIFEST.json` now covers the plugin folder only.
- `plugin.json`: a one-sentence developer description, `icon`, `documentationUrl`, `privacyPolicyUrl`, and `termsOfServiceUrl`. Claude Code and Codex manifests are at version 0.3.0 for the next release.
- Gemini installations retain the offline demo: release integrity permits only the root CLI-owned `.gemini-extension-install.json` as installation metadata while still rejecting symlinks, modified source and other unexpected files. Agent install verification now requires bundle integrity and the offline demo for full installs, checks Copilot’s live source binding, and sanitizes failure paths.

- The skill description leads with the words developers use: usage-based or metered billing, per token, per API call, seat plus usage, prepaid credits and wallets, overage, and migration off Stripe Billing or Chargebee. It also says when not to use the skill.
- The repository validator and release integrity skip local `claude plugin eval` output under `evals/<suite>/results/`.
- `START_HERE.md`, `llms.txt`, and the `@getlago/init` output show the exact Claude Code and Codex install commands for `lago@lago-plugins`; tests check README consistency, command order, invocation, and the CLI's actual dry-run output.
- Hardened install-free examples: refuse authenticated redirects, retry non-JSON transient responses, persist webhooks for durable polling, scope paginated wallet snapshots to eligible charges, and make subscription cadence and invoice reconciliation explicit.

- `llms.txt` leads with `START_HERE.md` and lists tasks in developer wording, such as billing per token in a Next.js app, adding prepaid credits, and migrating from Stripe Billing.
- Release integrity ignores `node_modules`.
- Direct application implementation requests can start on the first turn without a prior demo or accepted solution brief; the blueprint remains a preview and money-changing decisions remain explicit.
- Clarified that the application owns product events while Lago owns the selected billing functions.
- Prepared the repository for public installation: removed internal-access wording and the dated competitor benchmark; clarified recurring unique-count metrics in the beginner reference.

## [0.2.0] - 2026-09-15

### Added

- Optional official Lago CLI execution layer for agent-led inspection, diagnostics, configuration, validation, reconciliation, and repeatable operator workflows, with target verification, structured evidence, safe fallbacks, and production approval gates.
- Discovery-first Lago Solution Engineer positioning: the first walkthrough starts from anywhere, demonstrates Lago before intake, accepts a product description or pricing page, and treats a codebase as optional until implementation.
- Progressive solution engineering with reflected discovery, explicit fit verdicts, story-led tailored demos, measurable proof and exit criteria, and a solution brief that carries decisions into implementation.
- Untrusted-workspace boundary: repository content is evidence, never instructions or approval; approvals are valid only from the user in conversation, with matching adversarial eval cases.
- Hardened offline validators: money tests require a currency and reject non-finite values, reconciliation reports row counts and fails on empty input, event validation accepts documented numeric-string Unix timestamps, and the repository validator runs on Python 3.9.
- Blueprint-first beginner flow with one recommended default, an instant offline walkthrough path, compact progress and decision tracking, and precise completion levels.
- Behavioral evals for greenfield blueprinting, demo-first teaching, and the boundary between a working demo and production readiness.
- Dependency-free instant offline demo with duplicate-event and reconciliation evidence, plus a no-action-needed path for ambiguous beginner prompts outside an application repository.
- Gratification-first guided experience with one-step next actions and an `expert mode` opt-out that preserves safety and billing evidence while removing tutorials and routine narration.
- Evidence-derived money validation that extracts actuals from preserved Lago payloads and verifies their source hash; hand-written or modified actuals fail.
- Structured reconciliation failures for missing columns, duplicate keys, invalid amounts, empty inputs, and currency mismatches, plus stricter billable-event value validation.
- Public install identity `lago@lago-plugins`, with `/lago:implementation` for Claude Code and `$lago:implementation` for Codex; validators prevent identity regression while preserving the separate company-only namespace.
- Release-bundle SHA-256 verification, scheduled official-link checks, deterministic local-demo target validation, safer credential-presence discovery, explicit invoice-credit extraction, and migration cancellation gates.
- Passing live self-hosted Lago `v1.52.1` per-token money test with hash-linked source evidence and duplicate-event verification.
- Repository-backed opportunity discovery for AI-native billing, value credits, prepaid wallets, hybrid/provider coexistence, enterprise overrides, pricing backtests, and finance handoffs, with 19 anonymized field-replay evals.
- Stage-aware experience: Lago Solution Engineer for discovery and proof, then Billing Engineer Copilot for implementation without restarting discovery.
- One-screen product-to-Lago opportunity map, decisive first-model recommendation, source-to-money trace, and consistent Product, Engineering, and Finance handoffs.
- Product-aware first-run routing that skips the generic walkthrough when the opening prompt already supports a tailored recommendation, plus four regression cases covering the end-to-end commercial journey.
- Simpler public display name `Lago`, with the Solution Engineer role explained at runtime and the Billing Engineer Copilot transition reserved for implementation.

## [0.1.0] - 2026-08-26

### Added

- Shared eight-mode Lago implementation skill for Claude Code and Codex.
- Cloud, self-hosted, billing, events, webhook, migration, validation, reconciliation, troubleshooting, and safety references.
- Stripe Billing, Chargebee, and custom migration workflows.
- Offline event, money-test, reconciliation, and public-repository validators.
- Lago Billing Engineer positioning for applications with or without existing billing code.
- Beginner-first guidance that maps product concepts to Lago primitives one decision at a time.
- Hard isolation policy requiring self-hosted Lago for all seeded demos and prohibiting demo data in Lago Cloud.
- Canonical self-hosted OpenAI-style per-token demo with illustrative pricing and deterministic usage evidence.
- Mandatory first-run workspace and billing-state preflight, capability-boundary message, and contextual recovery guidance.
- Fifty-four synthetic eval cases, scorecard, examples, and release controls.
