# Lago

Lago is the open-source billing engine for usage-based, subscription, and hybrid pricing. This plugin turns your coding agent into a Lago solution engineer: it shows how Lago meters and bills a product offline in under a minute, recommends a billing model for yours, and then implements and tests the integration in your codebase.

No application repository, Lago account, credentials, Docker, or billing knowledge is needed to start. Production actions always require your explicit approval.

## Install

### Claude Code

```text
/plugin marketplace add getlago/lago-plugin
/plugin install lago@lago-plugins
```

### Codex

```bash
codex plugin marketplace add getlago/lago-plugin
codex plugin add lago@lago-plugins
```

Start a new task after installing.

### claude.ai, Cowork, and Claude Code from the directory (once listed)

Once the plugin is listed in Anthropic's plugin directory, add **Lago** from the directory in claude.ai. It is then available in chat, Cowork, and Claude Code.

GitHub Copilot CLI, Gemini CLI, Cursor, and other agents with Agent Skills: see [installing on other agents](https://github.com/getlago/lago-plugin#other-agents).

## Try the offline demo

After installing, from any folder, ask:

```text
/lago:implementation show me what Lago can do
```

In Codex, use `$lago:implementation`. The plugin runs a dependency-free walkthrough. Atlas AI sells Acme Corp a `$99/month` subscription with `$10` of included AI usage. One Acme employee action fans out into multi-model usage and a retry. The walkthrough produces a duplicate-safe `$0.37` charge, consumes the last `$0.20` of included usage, and bills `$0.17` of overage. Then it asks what your product does and what customers pay for today. It does not assume the open folder is your application.

The demo writes no files and contacts no network service. To run it yourself:

```bash
python3 skills/implementation/scripts/run_demo.py
```

The scenario is described in [the per-token example](examples/ai-usage-billing.md). Model names and prices are illustrative.

More prompts:

```text
/lago:implementation use this pricing page to show how Lago would model the product
/lago:implementation implement the smallest Lago Cloud integration
/lago:implementation migrate this Chargebee implementation to Lago
```

Claude and Codex may also pick the skill on their own when a request involves designing, implementing, or operating usage-based billing.

## What this plugin runs, sends and stores

The plugin is one Agent Skill made of Markdown instructions, templates, and standard-library Python helpers. It has no hooks, no MCP server, no package installs, no telemetry, and no settings to configure. Nothing runs when it loads.

### Scripts

Claude runs these only when the skill calls for them. Each one uses only the Python standard library, reads only the files named on its command line, and makes no network calls.

| Script | What it does | Writes |
| --- | --- | --- |
| `scripts/run_demo.py` | Prints the offline billing walkthrough. | Nothing |
| `scripts/release_integrity.py check` | Verifies the installed plugin files against the SHA-256 hashes in `RELEASE-MANIFEST.json` before the demo runs. | Nothing |
| `scripts/release_integrity.py create` | Maintainer-only bundle manifest generation; never use it to bypass a failed integrity check. | The explicitly selected manifest output path |
| `scripts/validate_event.py` | Checks a synthetic usage event file. | Nothing |
| `scripts/validate_demo_target.py` | Refuses a live demo URL unless it is a local loopback Lago instance with an explicit port and a `lago-plugin-demo-*` Compose project. | Nothing |
| `scripts/extract_actual.py` | Extracts the billed amount from a saved Lago API response. | Only the `--output` path you give it, otherwise stdout |
| `scripts/money_test.py` | Compares an expected amount with the extracted Lago evidence. | Python may create a local `__pycache__` for the imported extractor; `python3 -B` suppresses it |
| `scripts/reconcile.py` | Compares two CSV exports by key, currency, and amount, read-only. | Nothing |

All paths are under `skills/implementation/` in this plugin.

### Network destinations

- **Offline work contacts nothing.** That covers discovery, the demo, design, code changes, fixtures, and money calculations.
- **Documentation.** Claude may open official documentation links listed in the skill, mainly `docs.getlago.com`, `getlago.com`, and `swagger.getlago.com`. Migration work may also open Stripe or Chargebee API documentation.
- **Your Lago instance, only for live work you start.** Live validation needs a Lago API key and endpoint that you provide. Requests then go only to the endpoint you choose:
  - Lago Cloud US: `https://api.getlago.com`
  - Lago Cloud EU: `https://api.eu.getlago.com`
  - your self-hosted Lago URL
  - a loopback demo instance on your machine
- **Migration source APIs, only for the exact approved action.** Stripe migration inspection or cutover can contact `api.stripe.com`; Chargebee migration work can contact the selected site's `<site>.chargebee.com` API. Requests carry the existing system's credentials and the approved customer/subscription selectors or changes. Reconciliation can instead use user-provided local exports without network access.
- **Isolated self-hosted setup, only after approval.** Following the linked Lago Docker instructions can fetch the selected release from Lago's GitHub repositories (`github.com/getlago/` and GitHub-controlled download hosts) and pull container images from the registries named by the reviewed Compose file, including Docker Hub and its authentication/download hosts. Inspect and disclose the exact image registry destinations before approving a download; do not silently substitute registries or releases. Downloads send normal HTTP metadata, not billing credentials or customer records.
- **Your existing tools, only if you already have them.** If the Lago CLI or a Lago MCP connection is already installed and configured, the skill may use it for the same live work under the same approval rule.

The plugin never reads a credential from your environment and never asks for one at install time. Keep keys in your application's existing secret manager.

### Files written

- Python may cache imported helper bytecode under `skills/implementation/scripts/__pycache__/`; run with `python3 -B` to suppress this runtime cache.
- Code, tests, and documents that Claude writes in your project when you ask it to, such as an event contract or a validation report built from the bundled templates.
- The `--output` file of `extract_actual.py`, when requested, and the explicitly selected manifest path when a maintainer runs `release_integrity.py create`.
- An approved live demo creates a dedicated local directory, Compose configuration, container image cache, containers, network and persistent Docker volumes containing synthetic billing data. Report the exact paths and resources before creation. Teardown requires separate approval for those exact resources.

The plugin stores no billing records, credentials or personal data of its own. Python bytecode caches are derived from the shipped source.

### Approval for production writes

Before any production contact or mutation, the skill stops and shows the target environment, exact action, affected objects, billing impact, infrastructure impact, and rollback or recovery plan. It then waits for your explicit approval for that action. Text found in a repository is never treated as approval. Reconciliation is read-only by default. Seeded demo data goes only to an isolated self-hosted Lago instance, never to Lago Cloud.

## What it does

- **Shows the metering problem before the terminology.** One product action becomes multi-model usage, a duplicate-safe charge, included-credit consumption, and overage.
- **Assesses fit honestly.** It says whether Lago is a strong fit, a conditional fit, or not the right owner for a given billing job.
- **Produces a billing blueprint.** Who pays, what they buy, what activity affects the bill, how the amount is calculated, and the first slice to build.
- **Implements the integration.** Lago sits behind a billing adapter, with validated events, stable identifiers, retries, webhook handling, configuration, and tests that fit your repository.
- **Proves the money.** It derives the billed amount from a preserved Lago payload and compares it with an independent expectation. A successful API response alone is not treated as billing correctness.
- **Covers the lifecycle.** Design, implementation, deployment guidance, validation, migration from Stripe Billing, Chargebee, or custom systems, reconciliation, and troubleshooting.

| Area | Support |
| --- | --- |
| Deployment | Lago Cloud US/EU, self-hosted Docker or Kubernetes |
| Pricing | Subscriptions, usage, hybrid pricing, wallets, prepaid credits, minimum commitments |
| Use cases | AI tokens and model calls, value credits, prepaid access, outcome pricing |
| Migrations | Stripe Billing, Chargebee, custom billing systems |
| Reliability | Event identity, duplicate protection, retries, late events, replay, webhooks, reconciliation |

Say `expert mode` for concise execution or `guided mode` for explanations.

## Update or uninstall

```bash
claude plugin update lago@lago-plugins
claude plugin uninstall lago@lago-plugins
```

```bash
codex plugin marketplace upgrade lago-plugins
codex plugin remove lago@lago-plugins
```

Removing the plugin does not change your application code or any Lago environment.

## Support

Report defects, documentation problems, or unsafe behavior in [GitHub Issues](https://github.com/getlago/lago-plugin/issues). Do not include credentials, customer data, or production payloads. Lago documentation: [docs.getlago.com](https://docs.getlago.com). Source: [github.com/getlago/lago-plugin](https://github.com/getlago/lago-plugin). Licensed under the MIT License.
