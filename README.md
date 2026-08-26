# Lago for Coding Agents

A public, credential-free plugin that helps Claude Code and Codex assess, design, implement, deploy, migrate, validate, reconcile, and troubleshoot [Lago](https://www.getlago.com) integrations.

One shared skill supports Lago Cloud and self-hosted deployments, greenfield and existing applications, subscriptions, usage pricing, prepaid credits and wallets, minimum commitments, hybrid pricing, multi-tenancy, and migrations from Stripe Billing, Chargebee, or custom billing systems. Version 1 does not claim migration support for other providers.

## Install

### Claude Code

After this repository is public:

```text
/plugin marketplace add getlago/lago-agent-plugin
/plugin install lago@getlago
```

For local development:

```bash
git clone https://github.com/getlago/lago-agent-plugin.git
claude --plugin-dir ./lago-agent-plugin
```

Validate with `claude plugin validate ./lago-agent-plugin`. Invoke explicitly as:

```text
/lago:implementation assess this repository for a Lago integration
/lago:implementation implement the smallest Lago Cloud sandbox flow
/lago:implementation migrate this Chargebee implementation to Lago
```

Claude may also select the skill automatically from a clear Lago implementation request.

### Codex

After this repository is public:

```bash
codex plugin marketplace add getlago/lago-agent-plugin
codex plugin add lago@getlago
```

Start a new Codex task after installation. Invoke explicitly as:

```text
$lago:implementation design usage-based billing for this application
$lago:implementation prepare a self-hosted Kubernetes deployment
$lago:implementation migrate this Stripe Billing integration to Lago
```

Codex also discovers the skill automatically when the request matches its description. Current Codex plugin invocation is `$plugin:skill`; standalone skills use `$skill-name`.

## How it works

The `implementation` skill infers one or more modes: `assess`, `design`, `implement`, `deploy`, `migrate`, `validate`, `reconcile`, and `troubleshoot`. It discovers the repository first, separates facts from assumptions, keeps provider calls behind a billing adapter, and validates the billed amount with a deterministic money test.

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

The 34 synthetic cases and scorecard are in [evals/implementation](evals/implementation). A live money test additionally requires a separately approved Lago sandbox; never point evals at production.

## Updating and uninstalling

Pull a tagged release, then update through the installed marketplace. For Claude Code use `claude plugin update lago@getlago`; for Codex refresh the marketplace with `codex plugin marketplace upgrade getlago` and reinstall with `codex plugin add lago@getlago`. Start a new task after an update.

Uninstall with `claude plugin uninstall lago@getlago` or `codex plugin remove lago@getlago`. Removing the plugin does not change application code or any Lago environment.

## Troubleshooting

- Skill absent: verify the manifest, marketplace, installation, and start a new task. Claude local development can use `--plugin-dir` and `/reload-plugins`.
- Wrong Cloud endpoint: confirm region; current documented bases are `https://api.getlago.com` (US) and `https://api.eu.getlago.com` (EU).
- No credentials: offline assess/design/code/fixtures still work; report live behavior as unverified.
- Validation failure: run the repository validator, then platform validators, and fix the first structural error.

Authoritative sources: [Lago docs](https://docs.getlago.com), [Lago API](https://docs.getlago.com/api-reference/intro), [Lago OpenAPI](https://swagger.getlago.com/openapi.yaml), [Claude Code plugins](https://code.claude.com/docs/en/plugins), and official OpenAI Codex documentation plus the installed `codex plugin --help` for the current CLI.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Releases follow [RELEASING.md](RELEASING.md). Licensed under the [MIT License](LICENSE).
