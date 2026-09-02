# Lago Solution Engineer

Meet a Lago Solution Engineer first, then a Billing Engineer Copilot when you are ready to build. It makes [Lago](https://www.getlago.com) tangible in under a minute, maps the strongest billing opportunity for your product, and carries the accepted design into a testable integration from Claude Code or Codex.

You can start anywhere. No application repository, Lago account, credentials, Docker, or billing knowledge is required to explore Lago. Describe a product, share a pricing page, or run the built-in example; open a codebase only when you want repository-specific implementation.

This repository is internal while version `0.1.0` is under review. The intended end state is a public, Lago-maintained plugin after human, legal/brand, publisher, marketplace, and minimum-platform decisions are complete. Re-run the public-content audit against the exact release commit immediately before changing repository visibility or submitting it to a public marketplace; the current audit describes only the reviewed internal tree.

## What it does

- **Shows the metering problem before the terminology:** Atlas AI—the merchant—turns one Acme employee action into multi-model usage, a duplicate-safe charge, included-credit consumption, and overage. The plugin shows what the merchant avoids building before revealing Lago's model.
- **Understands a product at any depth:** starts from a product description or pricing page, and inspects customer, tenant, subscription, usage, and billing code only when a repository is explicitly in scope.
- **Assesses fit honestly:** reflects the desired outcome and current constraints, then says whether Lago is a strong fit, a conditional fit, or not the right owner for the job.
- **Turns demos into evidence:** tailors one product story and defines the smallest proof with business, technical, and exit criteria before implementation.
- **Produces a billing blueprint:** shows who pays, what they buy, what activity affects the bill, how the amount is calculated, and the first implementation slice.
- **Finds monetization opportunities:** identifies a recommended first model from real product behavior, with special guidance for AI usage, value credits, prepaid wallets, hybrid pricing, and existing-provider coexistence.
- **Implements the integration:** keeps Lago behind a billing adapter and adds validated events, stable identifiers, retry behavior, webhook handling, configuration, and tests that fit the repository.
- **Speaks to every buyer from one source of truth:** translates the same design and money evidence for Product, Engineering, and Finance without changing assumptions between teams.
- **Proves the money:** derives the actual result from a preserved Lago payload, hash-links the evidence, and compares it with an independently calculated expectation. Compilation, a successful API response, or two hand-written matching files are not treated as billing correctness.
- **Handles the full lifecycle:** supports design, implementation, deployment guidance, validation, migration, reconciliation, and evidence-led troubleshooting.

No prior Lago or billing expertise is required.

## Start here

After installation, from any task or folder, ask:

```text
show me what Lago can do
```

The plugin immediately runs a dependency-free offline example. Atlas AI sells Acme Corp a `$99/month` subscription with `$10` of included AI usage. One Acme employee action fans out into multi-model, input/output usage and a retry; the walkthrough produces a duplicate-safe `$0.37` charge, consumes the last `$0.20` of included usage, and calculates `$0.17` of overage. It shows the complete source-to-money path and what Atlas avoids building, then asks one question: `What does your product do, and what do customers pay for today?` It does not assume the open folder is your application.

To make the next walkthrough relevant, describe your product in one sentence or share its pricing page. When you are ready to implement, open the application repository and ask:

```text
implement Lago
```

Only then does the plugin inspect the codebase, recommend the smallest coherent billing slice, and ask about decisions that materially change money, architecture, lifecycle behavior, or authorization.

### Guided or concise

The default experience is hands-on and guided. Lago concepts are explained only when they become relevant, and every response ends with one clear next step.

Say `expert mode`, `skip the walkthrough`, or `just do it` for concise execution. The plugin will omit primers and routine narration while preserving material decisions, diffs, tests, risks, approvals, and money evidence. Say `guided mode` to restore explanations.

## Install

### Claude Code

```text
/plugin marketplace add getlago/lago-agent-plugin
/plugin install lago@getlago
```

Example prompts:

```text
/lago:implementation show me what Lago can do
/lago:implementation use this pricing page to show how Lago would model the product
/lago:implementation implement the smallest Lago Cloud integration
/lago:implementation migrate this Chargebee implementation to Lago
```

For local plugin development:

```bash
git clone https://github.com/getlago/lago-agent-plugin.git
claude --plugin-dir ./lago-agent-plugin
```

### Codex

```bash
codex plugin marketplace add getlago/lago-agent-plugin
codex plugin add lago@getlago
```

Start a new Codex task after installation. Example prompts:

```text
$lago:implementation show me what Lago can do; do not assume this workspace is my application
$lago:implementation use my product description to recommend one Lago billing model
$lago:implementation design usage-based billing for this application
$lago:implementation prepare a self-hosted Kubernetes deployment
```

Claude and Codex may also select the skill automatically when a request involves discovering, designing, implementing, or operating Lago billing.

## What happens after a prompt

1. **Discovery first:** without product context, completes the offline example without treating the current folder as the user's product; with useful context, goes straight to a tailored result.
2. **Progressive discovery:** asks one useful question at a time, reflects facts and assumptions, and stops as soon as it can assess fit.
3. **Opportunity map and solution brief:** maps who pays, what they buy, what behavior creates value, and Lago's billing job; recommends one model; and identifies the riskiest assumption.
4. **Smallest proof:** agrees on business, technical, evidence, and exit criteria before repository implementation or live validation.
5. **Implementation and handoff, when requested:** switches into Billing Engineer Copilot mode, inspects the explicitly scoped application, preserves the decision trail, validates behavior, and translates the result for Product, Engineering, and Finance.

An unrelated, empty, or documentation-only workspace does not block discovery. A repository becomes necessary only for a concrete code assessment or implementation; if it is missing then, the plugin explains why and gives one recovery action.

## Supported work

| Area | Support |
| --- | --- |
| Deployment | Lago Cloud US/EU and self-hosted Docker or Kubernetes guidance |
| Pricing | Subscriptions, usage, hybrid pricing, wallets, prepaid credits, and minimum commitments |
| Use-case discovery | AI tokens and model calls, value credits, prepaid access, outcome pricing, pricing backtests, and enterprise overrides |
| Application shape | Greenfield, existing billing integrations, and multi-tenant applications |
| Migrations | Stripe Billing, Chargebee, and custom billing systems |
| Reliability | Stable event identity, duplicate protection, retries, late events, replay, webhooks, and reconciliation |
| Operations | Validation, production-readiness gates, diagnosis, and rollback planning |

Version 1 does not claim migration support for providers other than Stripe Billing, Chargebee, and custom systems.

## Why MCP is optional

Discovery, product mapping, billing education, pricing-page analysis, offline examples, and money calculations need no application repository. Repository access becomes useful when implementing the adapter, connecting real product events, and fitting Lago into existing billing architecture.

Making MCP mandatory would put connection setup, authentication, and permissions in front of the first useful result. The plugin therefore works offline across Claude Code and Codex, for Lago Cloud and self-hosted deployments. When compatible Lago tools are already available, MCP may add supported live reads or explicitly approved actions, but it never gates the core experience and this repository does not bundle or duplicate it.

## Credentials, environments, and safety

No API key, MCP server, Docker runtime, package install, or custom telemetry is required to load the plugin or perform repository inspection, architecture work, code changes, fixtures, calculations, and offline tests.

Production contact or mutation always requires separate approval for the exact environment, action, affected objects, billing impact, infrastructure impact, and recovery plan. Reconciliation is read-only by default and never repairs discrepancies automatically.

Lago has no built-in sandbox. Offline examples contact no Lago runtime. Any seeded live demo must use a dedicated, version-pinned self-hosted Lago instance with isolated containers, ports, networks, and volumes. The plugin never seeds generic demo data into Lago Cloud, including an account called development, test, or staging.

Validation of a user’s real Lago environment is separate from a demo and requires explicit access and approval. Application credentials belong in the repository’s existing secret manager and must never be committed.

## Canonical offline demo

The bundled [OpenAI-style per-token example](examples/per-token-ai.md) uses illustrative model names and prices. It follows one AI research action through four deterministic token records, replays a duplicate, reconciles 21,000 tokens, and verifies a `$0.37` gross usage charge. Against Atlas Pro's illustrative `$99` subscription and charge-restricted `$10` wallet grant, the job consumes Acme's last `$0.20` and produces `$0.17` of overage, for `$99.17` billed before tax across the period. Archived live self-hosted evidence validates the complete one-period result: a `$99.00` subscription invoice plus a `$0.17` usage invoice after `$10.00` of eligible wallet credit. Invoice count depends on billing cadence. Automated monthly wallet renewal is edition-dependent and is not claimed by this proof. No payment or tax behavior is simulated.

Run it directly while developing the plugin:

```bash
python3 skills/implementation/scripts/run_demo.py
```

This writes no files and contacts no external service. Optional live validation follows the isolated self-hosted policy above and must not claim to reproduce current OpenAI pricing.

## Local development and validation

Python 3.9+ is required only for the deterministic helpers. The skill itself is Markdown.

```bash
python3 skills/implementation/scripts/validate_repo.py .
python3 -m unittest discover -s tests -v
python3 skills/implementation/scripts/release_integrity.py check . --manifest RELEASE-MANIFEST.json
claude plugin validate .
```

Live money validation preserves the Lago payload, generates `actual.json` with `extract_actual.py`, and verifies the source hash with `money_test.py --actual-source`. The repository includes 99 synthetic behavioral cases and deterministic tests for event validation, evidence-derived money calculations, reconciliation, first-run guidance, product-to-Lago opportunity mapping, stage transition, buyer-specific handoff, visible customer-to-money transformation, balanced fit assessment, controlled vendor positioning, rejection recovery, solution discovery, tailored demonstrations, proof planning, the offline demo, and environment safety. See the [eval suite](evals/implementation), [architecture decision](docs/architecture.md), and [benchmark](docs/benchmark.md).

## Update or uninstall

Claude Code:

```bash
claude plugin update lago@getlago
claude plugin uninstall lago@getlago
```

Codex:

```bash
codex plugin marketplace upgrade getlago
codex plugin add lago@getlago
codex plugin remove lago@getlago
```

Start a new task after an update. Removing the plugin does not change application code or a Lago environment.

## Troubleshooting

- **Skill not available:** verify the marketplace and installation, then start a new task. Claude local development can use `--plugin-dir` and `/reload-plugins`.
- **No credentials:** continue with repository implementation, fixtures, calculations, and offline tests. Live runtime behavior remains unverified.
- **Wrong Lago Cloud endpoint:** confirm the region. Current documented bases are `https://api.getlago.com` for US and `https://api.eu.getlago.com` for EU.
- **Validation failure:** run the repository validator, then platform validators, and fix the first structural error.
- **Bundle-integrity failure:** do not run bundled helpers. Reinstall from the verified Lago release or inspect the unexpected file change before regenerating the manifest.

Authoritative sources: [Lago documentation](https://docs.getlago.com), [Lago API reference](https://docs.getlago.com/api-reference/intro), [Lago OpenAPI](https://swagger.getlago.com/openapi.yaml), [Claude Code plugins](https://code.claude.com/docs/en/plugins), and official OpenAI Codex documentation plus the installed `codex plugin --help` for current CLI behavior.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Releases follow [RELEASING.md](RELEASING.md). Licensed under the [MIT License](LICENSE).
