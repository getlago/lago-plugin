# Lago Billing Engineer

A public, credential-free billing engineer copilot for Claude Code and Codex. It designs, implements, validates, migrates, reconciles, and troubleshoots [Lago](https://www.getlago.com) billing in applications with or without an existing billing integration.

One shared skill supports Lago Cloud and self-hosted deployments, greenfield and existing applications, subscriptions, usage pricing, prepaid credits and wallets, minimum commitments, hybrid pricing, multi-tenancy, and migrations from Stripe Billing, Chargebee, or custom billing systems. Version 1 does not claim migration support for other providers.

## Before you start

Open the application repository you want to change before invoking the plugin. The plugin inspects and edits local files; it does not locate or clone private applications automatically.

- No Lago credentials, MCP connection, or running Lago instance are required for repository inspection, architecture work, code changes, fixtures, or offline tests.
- Live sandbox validation requires Lago access later. The plugin will state exactly when it reaches that boundary.
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
/lago-billing:implementation implement the smallest Lago Cloud sandbox flow
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
3. **No credentials:** it continues with offline architecture, code, mocks, fixtures, calculations, and tests. Live runtime behavior is clearly marked unverified until sandbox access is available.
4. **Wrong or empty folder:** it states the inspected path and evidence, then asks you to open the application repository or provide its path. It does not search broadly or clone private code.
5. **Sandbox versus production:** sandbox reads or writes require available tools or credentials. Any production contact or mutation pauses for separate approval that names the target, action, scope, billing impact, and recovery plan.

Typical successful first response:

> Lago Billing Engineer loaded.
>
> I’m working in `/path/to/app`, a Node.js application.
>
> I can inspect and edit this repository without Lago credentials. Live sandbox validation requires credentials later, and production actions require separate approval.
>
> I’ll first map the existing customer, subscription, and usage architecture.

If the application has no billing integration yet, the response changes accordingly:

> Lago Billing Engineer loaded.
>
> I’m working in `/path/to/app`, a Node.js application. I found customer and authentication models, but no existing billing integration.
>
> I can design and implement the initial Lago integration without credentials. Live sandbox validation requires Lago access later.
>
> I’ll first determine the customer identity and smallest billable workflow, then ask for the first business decision that cannot be inferred from the code.

## How it works

The `implementation` skill infers the work required without asking users to choose an internal mode. It confirms activation, discovers the repository first, separates facts from assumptions, keeps provider calls behind a billing adapter, and validates the billed amount with a deterministic money test.

- Lago Cloud: region-aware US/EU endpoints, sandbox-first integration, no generated Lago infrastructure.
- Self-hosted: official Docker path for evaluation and official Helm path for Kubernetes; production adds explicit persistence, backup/restore, health, observability, upgrade, and rollback gates.
- Stripe/Chargebee: mapping ledger, historical-record retention, restartable checkpoints, parallel validation, and double-billing prevention.
- Reconciliation: read-only comparison by stable external IDs, event keys, periods, quantities, and amounts.

See [examples](examples), the [architecture decision](docs/architecture.md), and the [benchmark](docs/benchmark.md).

## Credentials, safety, and MCP

No API key, MCP server, Docker runtime, package install, or custom telemetry is needed to load this plugin or perform offline work. Never commit credentials. Application integrations should use the repository's existing secret manager and least privilege.

The skill pauses immediately before production contact or mutation and asks for approval for the exact target, action, objects, billing impact, infrastructure impact, and recovery plan. Reconciliation never repairs automatically.

Lago MCP is optional. When compatible tools exist, they may add supported live reads or explicitly approved actions; offline and live validation remain separate claims. This repository does not bundle or duplicate MCP.

## Local development and tests

Python 3.10+ is required only for the deterministic helpers; the skill itself is Markdown.

```bash
python3 skills/implementation/scripts/validate_repo.py .
python3 -m unittest discover -s tests -v
claude plugin validate .
python3 /path/to/plugin-creator/scripts/validate_plugin.py .
```

The 42 synthetic cases and scorecard are in [evals/implementation](evals/implementation). A live money test additionally requires a separately approved Lago sandbox; never point evals at production.

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
