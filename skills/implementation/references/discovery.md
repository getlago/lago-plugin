# Discovery and intake

## Silent preflight

Inspect, without asking first: root instructions; languages/frameworks/package managers; application boundaries; customer/account/organization/tenant and auth models; billing/subscription/provider code; usage producers and analytics; workers/queues; database/migrations; webhook endpoints; payment and tax integrations; deployment/secrets; tests/CI; logs/metrics/alerts.

Use targeted searches for `billing`, `subscription`, `invoice`, `usage`, `meter`, `stripe`, `chargebee`, `webhook`, `tenant`, `customer`, `wallet`, `credit`, `tax`, and environment URL/key names. Do not print secret values.

Classify the workspace before choosing work:

| Workspace evidence | Classification | Next action |
| --- | --- | --- |
| Application manifests plus source/runtime entrypoints | Application repository | Name the stack and inspect domain/billing architecture. |
| Workspace manifest with several apps/packages | Monorepo | Map candidates and infer the target from the prompt and relevant code; ask only if multiple targets remain plausible. |
| Immediate child folders contain separate application repositories | Multiple candidates | List the plausible candidates and evidence, then ask which one is the target. |
| Documentation generators, Markdown/content, or docs configuration without an application runtime | Documentation/content repository | Explain that application code is absent and give the exact recovery action. |
| No meaningful files | Empty folder | Explain that there is nothing to inspect and ask the user to open or provide the application repository. |
| Files exist but no application or repository boundary is supported by evidence | Wrong/unknown folder | State what was inspected and ask for the application path or a workspace change. |

Do not treat a package manifest alone as proof of an application; documentation sites and tooling repositories may also have one. Do not scan unrelated broad parent directories or attempt to locate, clone, or open private repositories automatically.

## First visible response

Adapt these prepared responses to the evidence. Preserve the first sentence exactly.

Application found:

> Lago plugin loaded.
>
> I’m working in `<path>`, a `<stack>` application.
>
> I can inspect and edit this repository without Lago credentials. `<Connected-tool status>` Live sandbox validation requires credentials later, and production actions require separate approval.
>
> I’ll first map the existing customer, subscription, and usage architecture.

Wrong, content-only, documentation, or empty folder:

> Lago plugin loaded, but the current folder is not an application repository. I inspected `<path>` and found `<evidence>`.
>
> Open the application repository in Codex, or give me its path. I do not locate or clone private applications automatically.

Multiple candidates:

> Lago plugin loaded. I inspected `<path>` and found multiple possible application repositories: `<candidates with evidence>`.
>
> I can work offline without Lago credentials, but I need the target application to avoid editing the wrong repository. Which candidate should I use?

Monorepo:

> Lago plugin loaded. I’m working in `<path>`, a `<stack>` monorepo. The likely application target is `<candidate>` because `<evidence>`.
>
> I can inspect and edit it without Lago credentials; live sandbox validation requires credentials later. I’ll map its customer, subscription, and usage boundaries first.

If a user expects live Lago access, state whether a Lago MCP/tool connection is actually available and whether credentials are configured. If either is absent, continue with offline repository work and identify the exact later step that requires sandbox access. Never use vague language such as “I need the repository path” without the inspected path, evidence, reason, and recovery action.

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

Ask only when the answer materially changes architecture, billing behavior, destructive scope, or production authorization. Ask one question at a time. Never infer commercial, legal, accounting, tax, or security requirements.

## Mode deliverables

- Assess: readiness, evidence, gaps, risks, recommended sequence; no file changes.
- Design: current/target diagrams, authority table, event contract, decisions and open questions.
- Implement/deploy/migrate: plan, reviewable changes, tests, rollback.
- Validate/reconcile: expected vs actual with preserved evidence.
- Troubleshoot: cause/evidence/hypotheses/telemetry/next check; no fix unless requested.
