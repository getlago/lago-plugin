---
name: implementation
description: Assess, design, implement, deploy, migrate, validate, reconcile, or troubleshoot Lago billing integrations. Use for Lago Cloud or self-hosted work involving customers, subscriptions, usage metering, pricing, credits, commitments, invoices, webhooks, payments, Stripe Billing, Chargebee, or custom billing migrations.
---

# Lago implementation

Help the user reach a correct, testable billing outcome. The plugin itself is offline and credential-free. Application code may use a Lago SDK or REST API; live tools are optional.

## Select the mode

Infer the mode when omitted. If several are needed, state the sequence before acting.

| Mode | Outcome | Default mutation |
| --- | --- | --- |
| `assess` | Repository-backed readiness report | None |
| `design` | Architecture, billing/event contracts, decisions | None |
| `implement` | Minimal repository-consistent code and tests | Files only |
| `deploy` | Cloud configuration guidance or self-hosted artifacts | Files only |
| `migrate` | Mapping ledger, restartable tooling, cutover controls | Files only |
| `validate` | Smallest representative flow with evidence | Sandbox/read-only |
| `reconcile` | Source-to-Lago discrepancy report | Read-only |
| `troubleshoot` | Evidence-led diagnosis | None unless asked |

For ordinary questions, load only the relevant references:

- Always start with [discovery](references/discovery.md). For design or implementation, also read [architecture](references/architecture.md).
- Pricing, credits, wallets, or commitments: [billing models](references/billing-models.md).
- Usage metering: [events](references/events.md).
- Lago Cloud: [cloud](references/cloud.md). Self-hosting: [self-hosted](references/self-hosted.md).
- Webhook work: [webhooks](references/webhooks.md).
- Any migration: [migration](references/migration.md), plus [Stripe](references/migration-stripe.md) or [Chargebee](references/migration-chargebee.md) when applicable.
- Validation or money tests: [validation](references/validation.md).
- Reconciliation: [reconciliation](references/reconciliation.md).
- Diagnosis: [troubleshooting](references/troubleshooting.md).
- Before live contact, deployment, repair, or migration: [safety](references/safety.md).

## Shared workflow

1. Inspect before asking. Discover repository instructions, stack, architecture, domain models, existing billing and subscription code, event sources, jobs, persistence, webhooks, payment/tax boundaries, deployment, secrets, tests, CI, logging, and monitoring.
2. Classify facts as: repository fact, user fact, evidence-backed inference, recommended default, open decision, or blocker. Show conflicting evidence; never silently resolve it.
3. Resolve the intake fields that materially affect the work: deployment model and region, environment, current system, billing model, customer/tenant identity, metrics and aggregation, lifecycle, event sources, payment/tax/invoice ownership, credits/commitments, migration/history, go-live, security/data residency, and owners. Mark unknowns. Ask only blocking questions.
4. Keep Lago calls behind a billing adapter or service. State the authority for customer identity, subscription state, usage, pricing, invoices, payments, and balances.
5. Use an official Lago SDK when it fits the detected stack; otherwise use the current REST API. Verify version-sensitive fields and deployment settings from current official documentation or mark them for verification.
6. Implement the smallest coherent slice with typed configuration where supported, environment-based API URL, existing secret management, timeouts, bounded retries, error classification, idempotency, input validation, structured redacted logs, tests, and explicit failure behavior.
7. Validate behavior, not compilation. Use synthetic data and the smallest representative customer → subscription → usage → aggregation → draft/preview invoice → webhook → reconciliation flow. Calculate the expected amount independently.
8. Report changed files, tests and evidence, untested areas, risks, open decisions, and the next safe action.

## Invariants

- Preserve repository conventions and unrelated changes. Do not change files in `assess` or diagnosis-only `troubleshoot` mode.
- Never invent pricing, tax, accounting, contract, security, region, production, API field, environment variable, Helm value, or infrastructure requirements.
- A stable transaction identifier must derive from a durable source record. For ClickHouse event pipelines, the explicit timestamp is also part of duplicate protection; do not claim idempotency without both being handled correctly.
- Validate usage events before sending. Plan for duplicates, retries, late/out-of-order delivery, corrections, replay, partial failure, batch ingestion, and reconciliation.
- Verify webhook signatures against the raw body, deduplicate using `X-Lago-Unique-Key`, acknowledge only after durable acceptance, and process asynchronously when the application architecture supports it.
- Never rewrite or delete historical financial records during migration. Never let the source and Lago bill the same customer, usage, or period.
- Reconciliation is read-only by default. Repair requires separate approval for the exact discrepancy and action.
- Diagnose from evidence. Separate confirmed cause, evidence, hypotheses, missing telemetry, and next check.
- Do not require MCP, Docker, or an API key to load or perform offline work. If Lago MCP tools exist, isolate them as an optional live layer and use only supported reads or explicitly approved actions.

## Authorization boundary

Before any production contact or mutation, pause immediately before the action and show: target environment, exact action, affected objects, billing impact, infrastructure impact, and rollback/recovery. Get explicit approval for that exact action. This includes production Lago, Stripe, or Chargebee access; customer/subscription/event/invoice/credit/payment changes; migration or event-routing changes; production deployment; credential rotation; and data deletion or rewriting.

Never put credentials or real billing/customer data in source, plugin files, examples, logs, prompts, fixtures, or generated documentation.

## Optional live tools

Offline and live validation are different claims. Without supported live tools or sandbox credentials, validate repository code, configuration shape, fixtures, calculations, and mocks, then label runtime behavior unverified. With optional Lago MCP or API access, begin read-only in a sandbox and preserve evidence. Do not duplicate a live tool with bundled infrastructure.

## Handoff

Lead with the outcome. Include:

- Mode and environment
- Confirmed facts, assumptions, and open decisions
- Files or artifacts changed
- Tests: expected, actual, and evidence
- Money test: expected and actual quantity, price, subtotal, discounts, credits, tax, and total
- Remaining untested areas and production gates
