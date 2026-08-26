# Discovery and intake

## Repository pass

Inspect, without asking first: root instructions; languages/frameworks/package managers; application boundaries; customer/account/organization/tenant and auth models; billing/subscription/provider code; usage producers and analytics; workers/queues; database/migrations; webhook endpoints; payment and tax integrations; deployment/secrets; tests/CI; logs/metrics/alerts.

Use targeted searches for `billing`, `subscription`, `invoice`, `usage`, `meter`, `stripe`, `chargebee`, `webhook`, `tenant`, `customer`, `wallet`, `credit`, `tax`, and environment URL/key names. Do not print secret values.

## Intake ledger

| Field | Evidence | Classification | Value/status |
| --- | --- | --- | --- |
| Deployment and region | | repository/user/inference/default/decision/blocker | |
| Environment | | | |
| Current billing system | | | |
| Customer identity and tenant boundary | | | |
| Pricing and metric requirements | | | |
| Subscription lifecycle | | | |
| Usage source and delivery guarantees | | | |
| Payment, tax, invoice ownership | | | |
| Credits, wallets, commitments | | | |
| Migration history and go-live | | | |
| Security, residency, owners | | | |

Ask only when the answer materially changes architecture, billing behavior, destructive scope, or production authorization. Never infer commercial, legal, accounting, tax, or security requirements.

## Mode deliverables

- Assess: readiness, evidence, gaps, risks, recommended sequence; no file changes.
- Design: current/target diagrams, authority table, event contract, decisions and open questions.
- Implement/deploy/migrate: plan, reviewable changes, tests, rollback.
- Validate/reconcile: expected vs actual with preserved evidence.
- Troubleshoot: cause/evidence/hypotheses/telemetry/next check; no fix unless requested.
