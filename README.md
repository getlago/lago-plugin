# Lago Billing Engineer

Turn a product’s pricing and usage model into a testable [Lago](https://www.getlago.com) integration from Claude Code or Codex.

The plugin works inside an application repository. It finds the customer and subscription boundaries, maps product behavior to Lago, implements the smallest coherent billing slice, and verifies the expected amount independently.

## What it does

- **Understands the application:** inspects customer, tenant, subscription, usage, webhook, payment, tax, and existing billing code before proposing changes.
- **Produces a billing blueprint:** shows who pays, what they buy, what activity affects the bill, how the amount is calculated, and the first implementation slice.
- **Implements the integration:** keeps Lago behind a billing adapter and adds validated events, stable identifiers, retry behavior, webhook handling, configuration, and tests that fit the repository.
- **Proves the money:** compares expected quantity and invoice amounts using exact deterministic calculations. Compilation or a successful API response is not treated as billing correctness.
- **Handles the full lifecycle:** supports design, implementation, deployment guidance, validation, migration, reconciliation, and evidence-led troubleshooting.

No prior Lago or billing expertise is required.

## Start here

After installation, open the application repository and ask:

```text
implement Lago
```

The plugin silently inspects the workspace, gives you the first useful result, recommends one path, and takes the next safe step. It asks only when a decision materially changes money, architecture, lifecycle behavior, or authorization.

Want to understand the flow first? Ask:

```text
help me start
show me a billing demo
```

The plugin immediately runs a dependency-free offline example with a product-to-Lago mapping, deterministic events, duplicate protection, reconciliation, and an exact `$0.37` money test. You do not need a Lago account, credentials, Docker, MCP, or even an application repository for this walkthrough.

### Guided or concise

The default experience is hands-on and guided. Lago concepts are explained only when they become relevant, and every response ends with one clear next step.

Say `expert mode`, `skip the walkthrough`, or `just do it` for concise execution. The plugin will omit primers and routine narration while preserving material decisions, diffs, tests, risks, approvals, and money evidence. Say `guided mode` to restore explanations.

## Install

### Claude Code

```text
/plugin marketplace add getlago/lago-agent-plugin
/plugin install lago-billing@lago-plugins
```

Example prompts:

```text
/lago-billing:implementation implement the smallest Lago Cloud integration
/lago-billing:implementation show me the offline per-token demo
/lago-billing:implementation migrate this Chargebee implementation to Lago
```

For local plugin development:

```bash
git clone https://github.com/getlago/lago-agent-plugin.git
claude --plugin-dir ./lago-agent-plugin
```

### Codex

```bash
codex plugin marketplace add getlago/lago-agent-plugin
codex plugin add lago-billing@lago-plugins
```

Start a new Codex task after installation. Example prompts:

```text
$lago-billing:implementation design usage-based billing for this application
$lago-billing:implementation prepare a self-hosted Kubernetes deployment
$lago-billing:implementation migrate this Stripe Billing integration to Lago
```

Claude and Codex may also select the skill automatically when a request clearly involves implementing or operating Lago billing.

## What happens after a prompt

1. **Workspace preflight:** confirms the repository, stack, application boundary, existing billing state, and available tools without printing credentials.
2. **First useful result:** produces a repository finding, billing blueprint, completed offline demo, code change, or verified test before collecting optional context.
3. **Smallest coherent implementation:** works through the application’s existing conventions and keeps provider calls behind a billing boundary.
4. **Behavior validation:** exercises a representative customer → subscription → usage → aggregation → invoice → webhook → reconciliation flow with synthetic data.
5. **Precise handoff:** distinguishes an offline example, repository implementation, live self-hosted validation, and actual production readiness.

If the current workspace is not an application, the plugin says what it inspected. A concrete implementation request gets one recovery action. A beginner or demo request gets the offline walkthrough first, so the first interaction is still useful.

## Supported work

| Area | Support |
| --- | --- |
| Deployment | Lago Cloud US/EU and self-hosted Docker or Kubernetes guidance |
| Pricing | Subscriptions, usage, hybrid pricing, wallets, prepaid credits, and minimum commitments |
| Application shape | Greenfield, existing billing integrations, and multi-tenant applications |
| Migrations | Stripe Billing, Chargebee, and custom billing systems |
| Reliability | Stable event identity, duplicate protection, retries, late events, replay, webhooks, and reconciliation |
| Operations | Validation, production-readiness gates, diagnosis, and rollback planning |

Version 1 does not claim migration support for providers other than Stripe Billing, Chargebee, and custom systems.

## Why MCP is optional

Most of the useful work happens in the application repository: understanding the data model, designing the billing flow, implementing the adapter, validating events, and testing the expected invoice amount.

Making MCP mandatory would put connection setup, authentication, and permissions in front of the first useful result. The plugin therefore works offline across Claude Code and Codex, for Lago Cloud and self-hosted deployments. When compatible Lago tools are already available, MCP may add supported live reads or explicitly approved actions, but it never gates the core experience and this repository does not bundle or duplicate it.

## Credentials, environments, and safety

No API key, MCP server, Docker runtime, package install, or custom telemetry is required to load the plugin or perform repository inspection, architecture work, code changes, fixtures, calculations, and offline tests.

Production contact or mutation always requires separate approval for the exact environment, action, affected objects, billing impact, infrastructure impact, and recovery plan. Reconciliation is read-only by default and never repairs discrepancies automatically.

Lago has no built-in sandbox. Offline examples contact no Lago runtime. Any seeded live demo must use a dedicated, version-pinned self-hosted Lago instance with isolated containers, ports, networks, and volumes. The plugin never seeds generic demo data into Lago Cloud, including an account called development, test, or staging.

Validation of a user’s real Lago environment is separate from a demo and requires explicit access and approval. Application credentials belong in the repository’s existing secret manager and must never be committed.

## Canonical offline demo

The bundled [OpenAI-style per-token example](examples/per-token-ai.md) uses illustrative model names and prices. It creates four deterministic token events across model and input/output filters, replays a duplicate, reconciles 21,000 tokens, and verifies an expected total of `$0.37`.

Run it directly while developing the plugin:

```bash
python3 skills/implementation/scripts/run_demo.py
```

This writes no files and contacts no external service. Optional live validation follows the isolated self-hosted policy above and must not claim to reproduce current OpenAI pricing.

## Local development and validation

Python 3.10+ is required only for the deterministic helpers. The skill itself is Markdown.

```bash
python3 skills/implementation/scripts/validate_repo.py .
python3 -m unittest discover -s tests -v
claude plugin validate .
```

The repository includes 50 synthetic behavioral cases and deterministic tests for event validation, money calculations, reconciliation, first-run guidance, the offline demo, and environment safety. See the [eval suite](evals/implementation), [architecture decision](docs/architecture.md), and [benchmark](docs/benchmark.md).

## Update or uninstall

Claude Code:

```bash
claude plugin update lago-billing@lago-plugins
claude plugin uninstall lago-billing@lago-plugins
```

Codex:

```bash
codex plugin marketplace upgrade lago-plugins
codex plugin add lago-billing@lago-plugins
codex plugin remove lago-billing@lago-plugins
```

Start a new task after an update. Removing the plugin does not change application code or a Lago environment.

## Troubleshooting

- **Skill not available:** verify the marketplace and installation, then start a new task. Claude local development can use `--plugin-dir` and `/reload-plugins`.
- **No credentials:** continue with repository implementation, fixtures, calculations, and offline tests. Live runtime behavior remains unverified.
- **Wrong Lago Cloud endpoint:** confirm the region. Current documented bases are `https://api.getlago.com` for US and `https://api.eu.getlago.com` for EU.
- **Validation failure:** run the repository validator, then platform validators, and fix the first structural error.

Authoritative sources: [Lago documentation](https://docs.getlago.com), [Lago API reference](https://docs.getlago.com/api-reference/intro), [Lago OpenAPI](https://swagger.getlago.com/openapi.yaml), [Claude Code plugins](https://code.claude.com/docs/en/plugins), and official OpenAI Codex documentation plus the installed `codex plugin --help` for current CLI behavior.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Releases follow [RELEASING.md](RELEASING.md). Licensed under the [MIT License](LICENSE).
