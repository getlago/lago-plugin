# Lago CLI execution layer

The official Lago CLI is an optional execution layer for agent-led Lago work. It is useful for broad API coverage, reproducible terminal workflows, machine-readable output, and evidence collection. It is not required to load the plugin, explore a billing model, edit an application, or run offline validation.

## Choose the right interface

| Need | Default interface |
| --- | --- |
| Application runtime integration | Official Lago SDK when it fits; current REST API otherwise |
| Agent-led inspection, diagnostics, catalog operations, validation, reconciliation, or scripts/CI | Lago CLI when already installed and configured |
| A supported operation already exposed as a connected native tool | That tool when it is safer or more direct |
| Offline discovery, design, fixtures, and money calculations | Plugin instructions and bundled helpers; no live interface |

Do not make application code shell out to `lago`. The CLI is an operator and agent interface, not an application transport. Do not duplicate the entire command reference in this plugin; the CLI is generated from Lago's OpenAPI specification and evolves independently.

## Preflight without side effects

1. Check whether `lago` exists with `command -v lago`. Do not install or update it without the user's approval.
2. When it exists, run `LAGO_NO_UPDATE_CHECK=1 lago version` and `lago --help`. Before an operation, run `lago <resource> --help` or `lago <resource> <action> --help`; never guess version-sensitive flags.
3. Inspect only credential names, profile names, configuration paths, and presence booleans. Never print configuration values or API keys.
4. Before live contact, apply [safety](safety.md). For an approved target, use `lago whoami --output json` and `lago doctor --output json` to verify the organization, resolved API URL, profile, region, and mode. A friendly profile name or `mode = "test"` is not proof that the target is isolated or safe.

If the CLI is absent or cannot establish the approved target, continue with offline work, an already-connected Lago tool, or SDK/REST implementation. State exactly which live claim remains unverified. Do not turn CLI installation into a prerequisite for the core plugin experience.

## Safe command behavior

- Prefer `--output json` for agent workflows and preserve sanitized raw JSON when it is evidence. Parse response envelopes as returned; do not scrape human-readable tables.
- Use `--query` only after checking the current response shape. Lago responses are wrapped by resource name, so queries must begin at that envelope.
- Use `--dry-run` to review a proposed write before asking for approval. A dry run is evidence of the planned request, not authorization to execute it and not proof of live behavior.
- Immediately before a live production request or any mutation covered by [safety](safety.md), show the exact target, command or API operation, object scope, billing impact, and recovery path, then obtain explicit approval for that operation.
- Treat the CLI's live-mode confirmation and `--confirm` controls as additional safeguards, not substitutes for conversational approval. Never weaken, bypass, or automate around them.
- Use `lago api` only when a named command is unavailable and the method, path, request body, and response shape have been verified from the current official API reference. It follows the same approval rules as named commands.
- Stop on every nonzero exit status. Classify the failure from structured output or the documented exit behavior; do not continue a multi-step billing workflow after a partial failure.
- Never include a credential literal in a command, diff, log, fixture, or prompt. Use the user's existing secret-management boundary without bringing the value into model context.

## Evidence and handoff

Record the CLI version, resolved target metadata, exact redacted command, exit status, sanitized response path or ID, expected result, actual result, and untested areas. For money validation, feed preserved Lago JSON into the repository's deterministic extraction and comparison flow; a successful CLI request alone does not prove billing correctness.

Sources: [Lago CLI overview](https://getlago.com/docs/guide/lago-cli/overview), [command reference](https://getlago.com/docs/guide/lago-cli/commands/overview), and [official repository](https://github.com/getlago/lago-cli).
