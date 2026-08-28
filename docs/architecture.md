# Architecture decision

## Decision

Ship one shared `implementation` skill with eight explicit modes and progressive references. Keep `.claude-plugin` and `.codex-plugin` as thin packaging layers. Bundle only standard-library offline validation scripts, synthetic templates, and evals.

## Why

- One skill preserves a single safety and billing-correctness contract across the lifecycle.
- Mode routing avoids overlapping commands while letting detailed references load only when needed.
- Credential-free offline work keeps installation low-friction and MCP optional.
- Deterministic event, money, reconciliation, demo-target, release-integrity, manifest, link, secret, and public-content checks provide evidence beyond prompt text.

## Boundaries

Application-generated code may call Lago through an official SDK or current REST API. The plugin never contacts Lago on load. Optional live tools remain isolated. Platform-specific behavior is limited to manifests, marketplace installation, and explicit invocation syntax.

The repository is named `lago-agent-plugin`, the shareable marketplace is `getlago`, and the plugin manifest identity is `lago`. This produces the approved install target `lago@getlago` and the invocation commands `/lago:implementation` in Claude Code and `$lago:implementation` in Codex. “Lago Billing Engineer” remains the user-facing product name.
