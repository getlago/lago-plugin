<img src="plugins/lago/assets/lago-logo.svg" alt="Lago logo" width="64" height="64">

# Lago plugin for coding agents

This repository holds the Lago plugin for Claude Code and Codex. It turns your coding agent into a Lago solution engineer: it shows how [Lago](https://www.getlago.com), the open-source billing engine, meters and bills a product offline in under a minute, recommends a billing model for yours, and implements and tests the integration in your codebase.

The shipped plugin lives in [`plugins/lago/`](plugins/lago). Its [README](plugins/lago/README.md) is the user guide: install steps for Claude Code, Codex, and the Anthropic plugin directory, the offline demo, and exactly what the plugin runs, sends, and stores. Everything else in this repository is tests, evals, documentation, and release tooling.

No plugin support in your agent, or nothing installed yet? Follow [START_HERE.md](START_HERE.md): one page with the offline demo and complete Node.js/TypeScript and Python integration code.

## Install

Claude Code and Codex: see [plugins/lago/README.md](plugins/lago/README.md#install).

## Other agents

### GitHub Copilot CLI

Copilot CLI reads the same marketplace as Claude Code. Run each command in your terminal:

```bash
copilot plugin marketplace add getlago/lago-plugin
copilot plugin install lago@lago-plugins
```

### Gemini CLI

Gemini CLI installs extensions only from a repository root, and the plugin now lives in `plugins/lago/`. Install the skill from the subfolder:

```bash
gemini skills install https://github.com/getlago/lago-plugin.git --path plugins/lago/skills/implementation
```

For the full extension with the bundled demo and integrity check, install from a clone:

```bash
git clone https://github.com/getlago/lago-plugin.git
gemini extensions install ./lago-plugin/plugins/lago
```

The integrity check permits only Gemini's root `.gemini-extension-install.json` bookkeeping file as an extra file; bundled code remains hash-checked. Goose documents support for the same `gemini-extension.json` format, but has not been tested here.

### Cursor

In Cursor, open **Customize**, choose **From GitHub Repository**, and enter `getlago/lago-plugin`. The repository ships `.cursor-plugin/marketplace.json`, which points at `plugins/lago/.cursor-plugin/plugin.json`.

### Other agents with Agent Skills

Any agent that reads `SKILL.md` from `.agents/skills/` can install the skill alone:

```bash
npx skills add getlago/lago-plugin --skill implementation
```

This copies only `plugins/lago/skills/implementation/`. Without the full plugin bundle, the skill cannot verify `RELEASE-MANIFEST.json`, so it shows the offline walkthrough from its reference instead of running the bundled demo script. Links to the plugin's `examples/` are also unavailable in a skill-only install; read those examples in this repository. Prefer a plugin or extension install when your agent supports one.

| Agent | Install path | Verified |
| --- | --- | --- |
| Claude Code, Codex | Plugin `lago@lago-plugins` | Claude Code triggering evals and Codex smoke checks, see [evals/triggers](evals/triggers/README.md) |
| GitHub Copilot CLI | Plugin `lago@lago-plugins` from `.claude-plugin/marketplace.json` | Local marketplace install, verified source binding, bundle integrity and offline demo, Copilot CLI 1.0.100 |
| Gemini CLI | Extension from `plugins/lago/gemini-extension.json` | Validation, install from `plugins/lago`, discovery, installed bundle integrity and offline demo, Gemini CLI 0.64.0. The `gemini skills install --path` command is not verified. |
| Cursor | `.cursor-plugin/` | Generated from Cursor's documented format; not tested in Cursor |
| Goose, Devin | Read `plugins/lago/gemini-extension.json` or `.claude-plugin/` per their docs | Not tested |
| skills.sh agents | Skill only | Install, skills 1.7.4 |

[docs/release-evidence/agents-2026-10-19](docs/release-evidence/agents-2026-10-19/README.md) records the commands and results. These installation checks do not demonstrate automatic selection or integration correctness on the new agents.

Format and installation references: [Copilot CLI](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference), [Gemini CLI](https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/extensions/reference.md), [Cursor manifests](https://cursor.com/docs/reference/plugins.md), [Cursor repository import](https://cursor.com/docs/rules), [Goose formats](https://raw.githubusercontent.com/aaif-goose/goose/main/documentation/docs/guides/context-engineering/plugins.md), and [Devin compatibility](https://docs.devin.ai/cli/extensibility/plugins).

## Why MCP is optional

Discovery, product mapping, billing education, pricing-page analysis, offline examples, and money calculations need no application repository. Repository access becomes useful when implementing the adapter, connecting real product events, and fitting Lago into existing billing architecture.

Making MCP mandatory would put connection setup, authentication, and permissions in front of the first useful result. The plugin therefore works offline across Claude Code and Codex, for Lago Cloud and self-hosted deployments. When compatible Lago tools are already available, MCP may add supported live reads or explicitly approved actions, but it never gates the core experience and this repository does not bundle or duplicate it.

## How the Lago CLI fits

The official [`lago` CLI](https://getlago.com/docs/guide/lago-cli/overview) is also optional. When it is already installed and configured, the plugin may use it for agent-led inspection, diagnostics, catalog operations, validation, reconciliation, and scripts that benefit from JSON output and reproducible commands. The plugin checks the installed command's help before using version-sensitive syntax, verifies the resolved target before approved live work, and applies the same production approval gates used for MCP or direct API access.

Application code still uses an official Lago SDK or the REST API; it never shells out to the CLI. The plugin does not install or update the CLI without approval, does not require it for offline work, and falls back to connected tools or SDK/REST implementation when it is unavailable.

## Credentials, environments, and safety

The user-facing disclosure is in [What this plugin runs, sends and stores](plugins/lago/README.md#what-this-plugin-runs-sends-and-stores).


No API key, Lago CLI, MCP server, Docker runtime, package install, or custom telemetry is required to load the plugin or perform repository inspection, architecture work, code changes, fixtures, calculations, and offline tests.

Production contact or mutation always requires separate approval for the exact environment, action, affected objects, billing impact, infrastructure impact, and recovery plan. Reconciliation is read-only by default and never repairs discrepancies automatically.

Lago has no built-in sandbox. Offline examples contact no Lago runtime. Any seeded live demo must use a dedicated, version-pinned self-hosted Lago instance with isolated containers, ports, networks, and volumes. The plugin never seeds generic demo data into Lago Cloud, including an account called development, test, or staging.

Validation of a user’s real Lago environment is separate from a demo and requires explicit access and approval. Application credentials belong in the repository’s existing secret manager and must never be committed.

## Canonical offline demo

The bundled [OpenAI-style per-token example](plugins/lago/examples/ai-usage-billing.md) uses illustrative model names and prices. It follows one AI research action through four deterministic token records, replays a duplicate, reconciles 21,000 tokens, and verifies a `$0.37` gross usage charge. Against Atlas Pro's illustrative `$99` subscription and charge-restricted `$10` wallet grant, the job consumes Acme's last `$0.20` and produces `$0.17` of overage, for `$99.17` billed before tax across the period. Archived live self-hosted evidence validates the complete one-period result: a `$99.00` subscription invoice plus a `$0.17` usage invoice after `$10.00` of eligible wallet credit. Invoice count depends on billing cadence. Automated monthly wallet renewal is edition-dependent and is not claimed by this proof. No payment or tax behavior is simulated.

Run it directly while developing the plugin:

```bash
python3 plugins/lago/skills/implementation/scripts/run_demo.py
```

This writes no files and contacts no external service. Optional live validation follows the isolated self-hosted policy above and must not claim to reproduce current OpenAI pricing.

## Local development and validation

Python 3.9+ is required only for the deterministic helpers. The skill itself is Markdown.

```bash
python3 scripts/validate_repo.py .
python3 -m unittest discover -s tests -v
python3 plugins/lago/skills/implementation/scripts/release_integrity.py check plugins/lago --manifest plugins/lago/RELEASE-MANIFEST.json
claude plugin validate plugins/lago
python3 scripts/check_directory_limits.py plugins/lago
```

Live money validation preserves the Lago payload, generates `actual.json` with `extract_actual.py`, and verifies the source hash with `money_test.py --actual-source`. The repository includes 100 synthetic behavioral cases and deterministic tests for event validation, evidence-derived money calculations, reconciliation, first-run guidance, product-to-Lago opportunity mapping, stage transition, buyer-specific handoff, visible customer-to-money transformation, balanced fit assessment, controlled vendor positioning, rejection recovery, solution discovery, tailored demonstrations, proof planning, optional CLI execution, the offline demo, and environment safety. See the [eval suite](evals/implementation), [architecture decision](docs/architecture.md).

## Troubleshooting

- **Skill not available:** verify the marketplace and installation, then start a new task. Claude local development can use `--plugin-dir` and `/reload-plugins`.
- **No credentials:** continue with repository implementation, fixtures, calculations, and offline tests. Live runtime behavior remains unverified.
- **Wrong Lago Cloud endpoint:** confirm the region. Current documented bases are `https://api.getlago.com` for US and `https://api.eu.getlago.com` for EU.
- **Validation failure:** run the repository validator, then platform validators, and fix the first structural error.
- **Bundle-integrity failure:** do not run bundled helpers. Reinstall from the verified Lago release or inspect the unexpected file change before regenerating the manifest.

Authoritative sources: [Lago documentation](https://docs.getlago.com), [Lago API reference](https://docs.getlago.com/api-reference/intro), [Lago OpenAPI](https://swagger.getlago.com/openapi.yaml), [Claude Code plugins](https://code.claude.com/docs/en/plugins), and official OpenAI Codex documentation plus the installed `codex plugin --help` for current CLI behavior.

## Contributing

Report defects in [GitHub Issues](https://github.com/getlago/lago-plugin/issues), without credentials, customer data, or production payloads. See [CONTRIBUTING.md](CONTRIBUTING.md). Releases follow [RELEASING.md](RELEASING.md). Licensed under the [MIT License](LICENSE).
