# Lago Billing Engineer

A public, beginner-friendly billing engineer copilot for Claude Code and Codex. It designs, implements, validates, migrates, reconciles, and troubleshoots [Lago](https://www.getlago.com) billing in applications with or without an existing billing integration.

One shared skill supports Lago Cloud and self-hosted deployments, greenfield and existing applications, subscriptions, usage pricing, prepaid credits and wallets, minimum commitments, hybrid pricing, multi-tenancy, and migrations from Stripe Billing, Chargebee, or custom billing systems. Version 1 does not claim migration support for other providers.

## Before you start

Open the application repository you want to change before invoking the plugin. The plugin inspects and edits local files; it does not locate or clone private applications automatically.

- No prior Lago or billing expertise is required. The copilot starts from your product—who pays, what they buy, and what usage matters—then explains Lago primitives as they become relevant.
- No Lago credentials, MCP connection, or running Lago instance are required for repository inspection, architecture work, code changes, fixtures, or offline tests.
- Lago has no built-in sandbox. Offline examples need no Lago access; any live seeded demo uses a dedicated self-hosted instance, never Lago Cloud.
- Production contact or mutation is never implied by installation or invocation and always requires separate explicit approval for the exact action.
- On first run, expect a short activation message confirming the workspace, detected stack, whether billing already exists, current capabilities, and first next step.

## Install

### Claude Code

After this repository is public:

```text
/plugin marketplace add getlago/lago-agent-plugin
/plugin install lago-billing@lago-plugins
```

For local development:

```bash
git clone https://github.com/getlago/lago-agent-plugin.git
claude --plugin-dir ./lago-agent-plugin
```

Validate with `claude plugin validate ./lago-agent-plugin`. Invoke explicitly as:

```text
/lago-billing:implementation assess this repository for a Lago integration
/lago-billing:implementation implement the smallest Lago Cloud integration
/lago-billing:implementation show the self-hosted per-token demo
/lago-billing:implementation migrate this Chargebee implementation to Lago
```

Claude may also select the skill automatically from a clear Lago implementation request.

### Codex

After this repository is public:

```bash
codex plugin marketplace add getlago/lago-agent-plugin
codex plugin add lago-billing@lago-plugins
```

Start a new Codex task after installation. Invoke explicitly as:

```text
$lago-billing:implementation design usage-based billing for this application
$lago-billing:implementation prepare a self-hosted Kubernetes deployment
$lago-billing:implementation migrate this Stripe Billing integration to Lago
```

Codex also discovers the skill automatically when the request matches its description. Current Codex plugin invocation is `$plugin:skill`; standalone skills use `$skill-name`.

## Five-minute quickstart

Invoke the plugin with a short request such as:

```text
implement Lago
```

The plugin silently inspects the workspace before responding. Then follow the path that matches what it finds:

1. **Existing application:** it confirms the repository and stack, maps existing customer, subscription, usage, billing, and provider code, then starts with the smallest repository-consistent change.
2. **Application without billing:** it confirms the stack and application boundary, states that no billing integration was found, identifies the minimum customer and billable workflow, and asks only the next blocking business decision.
3. **No credentials:** it continues with offline architecture, code, mocks, fixtures, calculations, and tests. Live runtime behavior is clearly marked unverified.
4. **Wrong or empty folder:** it states the inspected path and evidence, then asks you to open the application repository or provide its path. It does not search broadly or clone private code.
5. **Demo versus real environments:** a live seeded demo uses only an isolated self-hosted Lago instance. Lago Cloud—including staging—is never used for generic demo data. Validation against the user's real environment requires separate access and approval.

Typical successful first response:

> Lago Billing Engineer loaded.
>
> I’m working in `/path/to/app`, a Node.js application.
>
> I can inspect and edit this repository without Lago credentials. A live seeded demo would use isolated self-hosted Lago; validation of a real environment requires separate access and approval.
>
> I’ll first map who pays, what they buy, and what usage affects the bill. I’ll explain the corresponding Lago concepts as we use them.

If the application has no billing integration yet, the response changes accordingly:

> Lago Billing Engineer loaded.
>
> I’m working in `/path/to/app`, a Node.js application. I found customer and authentication models, but no existing billing integration.
>
> I can design and implement the initial Lago integration without credentials. A live seeded demo would use isolated self-hosted Lago; validation of a real environment requires separate access and approval.
>
> I’ll first determine who should be billed and the smallest product action that should affect their bill. I’ll explain how those map to Lago, then ask for the first business decision that cannot be inferred from the code.

### The primitives you will learn as needed

The copilot translates application concepts into a small core path: who pays becomes a Lago **customer**; the package and price become a **plan**; assigning that package creates a **subscription**; product activity becomes an **event**; a **billable metric** measures those events; a **charge** turns measured usage into money; and Lago produces an **invoice**. Wallets, coupons, commitments, and entitlements are introduced only when the product requires them.

## How it works

The `implementation` skill infers the work required without asking users to choose an internal mode. It confirms activation, discovers the repository first, separates facts from assumptions, keeps provider calls behind a billing adapter, and validates the billed amount with a deterministic money test.

- Lago Cloud: region-aware US/EU integration with no generic demo data. A Cloud account is one environment, not a built-in sandbox.
- Self-hosted: official, isolated Docker path for live demos and local evaluation; official Helm path for Kubernetes; production adds explicit persistence, backup/restore, health, observability, upgrade, and rollback gates.
- Stripe/Chargebee: mapping ledger, historical-record retention, restartable checkpoints, parallel validation, and double-billing prevention.
- Reconciliation: read-only comparison by stable external IDs, event keys, periods, quantities, and amounts.

See [examples](examples), the [architecture decision](docs/architecture.md), and the [benchmark](docs/benchmark.md).

## Credentials, safety, and MCP

No API key, MCP server, Docker runtime, package install, or custom telemetry is needed to load this plugin or perform offline work. Never commit credentials. Application integrations should use the repository's existing secret manager and least privilege.

The skill pauses immediately before production contact or mutation and asks for approval for the exact target, action, objects, billing impact, infrastructure impact, and recovery plan. Reconciliation never repairs automatically.

Lago MCP is optional. When compatible tools exist, they may add supported live reads or explicitly approved actions; offline and live validation remain separate claims. This repository does not bundle or duplicate MCP.

### Demo data policy

The copilot builds every example offline first. If the user asks for a live demo, it checks for Docker, explains the images, containers, ports, and disposable data involved, and asks before starting anything. It then uses a dedicated, version-pinned self-hosted Lago instance with isolated names, networks, and volumes. It refuses to seed fake customers or usage into any Lago Cloud account, even one dedicated to staging.

The default live walkthrough is an [OpenAI-style per-token demo](examples/per-token-ai.md), adapted from Lago's official template. It creates a synthetic AI customer, a token billable metric with model and input/output filters, a pay-as-you-go plan, a subscription, and deterministic token events. Prices and model names are explicitly illustrative; the demo verifies current usage and a $0.37 independent money calculation without claiming to reproduce current OpenAI pricing.

## Local development and tests

Python 3.10+ is required only for the deterministic helpers; the skill itself is Markdown.

```bash
python3 skills/implementation/scripts/validate_repo.py .
python3 -m unittest discover -s tests -v
claude plugin validate .
python3 /path/to/plugin-creator/scripts/validate_plugin.py .
```

The 45 synthetic cases and scorecard are in [evals/implementation](evals/implementation). A live demo money test additionally requires a separately approved isolated self-hosted Lago instance; never point evals at Lago Cloud or production.

## Updating and uninstalling

Pull a tagged release, then update through the installed marketplace. For Claude Code use `claude plugin update lago-billing@lago-plugins`; for Codex refresh the marketplace with `codex plugin marketplace upgrade lago-plugins` and reinstall with `codex plugin add lago-billing@lago-plugins`. Start a new task after an update.

Uninstall with `claude plugin uninstall lago-billing@lago-plugins` or `codex plugin remove lago-billing@lago-plugins`. Removing the plugin does not change application code or any Lago environment.

## Troubleshooting

- Skill absent: verify the manifest, marketplace, installation, and start a new task. Claude local development can use `--plugin-dir` and `/reload-plugins`.
- Wrong Cloud endpoint: confirm region; current documented bases are `https://api.getlago.com` (US) and `https://api.eu.getlago.com` (EU).
- No credentials: offline assess/design/code/fixtures still work; report live behavior as unverified.
- Validation failure: run the repository validator, then platform validators, and fix the first structural error.

Authoritative sources: [Lago docs](https://docs.getlago.com), [Lago API](https://docs.getlago.com/api-reference/intro), [Lago OpenAPI](https://swagger.getlago.com/openapi.yaml), [Claude Code plugins](https://code.claude.com/docs/en/plugins), and official OpenAI Codex documentation plus the installed `codex plugin --help` for the current CLI.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Releases follow [RELEASING.md](RELEASING.md). Licensed under the [MIT License](LICENSE).
