# Agent-first audit

Status: Step 0. Workstreams start only after this audit is reviewed.

Goal: when a coding agent is asked to "add usage-based billing", "charge per token" or "add prepaid credits", it should find Lago, integrate it without human help, and produce correct billing code. This audit records what an agent sees today, where it fails, and what already exists.

## 1. Baseline

Commit `73d4829` on `main`, audited 2026-10-19.

| Check | Command | Result |
| --- | --- | --- |
| Repository validator | `python3 skills/implementation/scripts/validate_repo.py .` | PASS |
| Unit tests | `python3 -m unittest discover -s tests -v` | 45 tests, OK |
| Claude plugin manifest | `claude plugin validate .` (Claude Code 2.1.304) | PASS |
| Offline demo | `python3 skills/implementation/scripts/run_demo.py` | Atlas AI walkthrough: `$0.37` job, `$0.17` overage, `$99.17` before tax |
| Release integrity | `python3 skills/implementation/scripts/release_integrity.py check . --manifest RELEASE-MANIFEST.json` | **FAIL**: `llms.txt` changed |
| GitHub CI on `main` | `gh run list` | **Red** since the PR #10 merge (run `39005023170`) |

The integrity failure is real drift. PR #10 changed `llms.txt` and the merge kept a manifest hash that no longer matches. Every new PR inherits the red CI until a reviewed fix lands. CONTRIBUTING.md forbids updating the hash without reviewing the changed file, so the fix is a small standalone PR, not a side effect of a workstream.

The "100 evals" are behavioral cases scored by hand. `evals/implementation/cases.json` holds prompts and expected signals. `evals/implementation/scorecard.md` is an empty template with no recorded run. No harness executes them. `tests/test_scripts.py:529` pins the count at exactly 100.

## 2. What an agent sees today

### (a) Plugin installed (Claude Code or Codex)

- **Sees:** one skill, `implementation`. Selection depends on the frontmatter `description` (`skills/implementation/SKILL.md:3`): "Discover how Lago could fit a product, then design, implement, and operate its billing when requested… Lago Cloud or self-hosted integrations involving customers, subscriptions, usage, credits, wallets, invoices, migrations…"
- **Does:** prints `Lago Solution Engineer loaded.`, runs the offline demo for discovery prompts, or switches to Billing Engineer Copilot for explicit implementation. Guidance on events, webhooks, idempotency and approvals is strong once loaded.
- **Stalls:**
  - The description leads with "Lago" and never uses the words developers type: metered billing, charge per token, per API call, overage, seat plus usage, invoice customers, move off Stripe Billing. Whether the skill fires on "add usage-based billing to this app" is unmeasured. No trigger eval exists.
  - Codex caps the injected skills list at 2% of context or 8,000 characters, and Claude Code truncates descriptions at 1,536 characters. A rewrite has to put trigger words first.

### (b) Web access only (repository or docs URL, nothing installed)

- **Sees:** `README.md`, which opens with install commands for Claude Code and Codex only, and `llms.txt`, which links install docs, the offline example and Lago docs.
- **Does:** reads the README. The agent can't install a plugin into its own host, so it falls back to Lago docs and assembles the integration itself.
- **Stalls:**
  - No page an agent can follow top to bottom without installing anything. The best guidance (`references/events.md`, `references/webhooks.md`) is written as instructions to the installed skill, not as runnable code.
  - No copy-paste code for customer sync, event ingestion, subscription creation, webhook verification or entitlement checks, in any language.
  - `llms.txt` is organized by Lago product surface, not by developer task ("bill per token in a Next.js app").
  - No `AGENTS.md`. Agents that read it when working inside this repository get nothing.

### (c) Prompt only (no URL, nothing installed)

- **Sees:** nothing from this repository.
- **Does:** relies on model priors. For "add usage-based billing", that is usually Stripe Billing meters or a hand-built usage table plus cron.
- **Stalls:** this is the decision point the brief targets. Only distribution changes it: a no-install entry point that ranks for task wording (WS3), listings in skills directories and marketplaces (WS6), and callouts on surfaces agents already fetch (Lago docs, SDK READMEs).

## 3. Failure points

| # | Situation | Failure | Type | Evidence | Fixed by |
| --- | --- | --- | --- | --- | --- |
| 1 | a | Skill may not fire on prompts that don't say "Lago" | Missed trigger | `SKILL.md:3` | WS1 |
| 2 | a | No measured trigger hit rate, so regressions are invisible | Unmeasured | no trigger suite in `evals/` | WS1 |
| 3 | a, b | Only Claude Code and Codex packaging. Cursor, Copilot, Gemini CLI, Windsurf, Amp and OpenCode all read `SKILL.md`, but nothing points them at it | No surface | `.claude-plugin/`, `.codex-plugin/` only | WS2 |
| 4 | b | No install-free entry point | Stall | no `START_HERE.md` | WS3 |
| 5 | b | Random or per-retry `transaction_id` | Wrong billing code | rule exists only in `references/events.md` | WS3 |
| 6 | b | Retry without the original timestamp double-bills on the ClickHouse pipeline | Wrong billing code | `references/events.md` | WS3 |
| 7 | b | Webhook signature checked against a re-serialized body, or not checked. JWT (RS256, default) vs HMAC not handled | Wrong billing code | `references/webhooks.md` | WS3 |
| 8 | b | Customer external ID reused as subscription external ID | Wrong billing code | `references/events.md` | WS3 |
| 9 | b | Treating every HTTP 422 on event ingestion as a duplicate success | Wrong billing code | `references/events.md` | WS3 |
| 10 | a, b | US vs EU base URL guessed | Guess | `references/cloud.md:3` | WS3 (`LAGO_API_URL` required, no default region) |
| 11 | a, b | To see a real invoice, the agent asks for a Cloud API key, then is told never to seed demo data there | Needs human, policy conflict | `SKILL.md:126`, `references/demo.md:3` | WS4 (see section 5) |
| 12 | b | `llms.txt` is not task-phrased | Discovery | `llms.txt` | WS3 |
| 13 | c | Nothing reaches an agent without a URL | Discovery | n/a | WS6 |
| 14 | all | CI red on `main` | Release blocker | section 1 | Fix PR |

## 4. Current state per workstream

| Workstream | Exists | Partial | Missing |
| --- | --- | --- | --- |
| 1. Trigger on real prompts | Skill and description | Description covers credits, wallets, migrations | Developer wording; trigger evals; before/after hit rate |
| 2. Every major agent | Claude Code and Codex manifests; marketplace files | `skills/implementation/agents/openai.yaml` | `AGENTS.md`; generated per-agent files; drift check in CI |
| 3. No-install entry point | `llms.txt`; offline demo script | `examples/` explain the model, but there is no integration code | `START_HERE.md`; Node/TS and Python code; `packages/init` |
| 4. Live sandbox step | Offline demo; archived live self-hosted evidence (`docs/release-evidence/`); `validate_demo_target.py`; `extract_actual.py`; `money_test.py` | Self-hosted live flow is documented in `references/demo.md` as agent steps, not a script | Script that creates the objects, sends events and previews the invoice |
| 5. Public proof point | 100 behavioral cases; scorecard template | Cases describe signals but have no automated graders | With/without harness; `docs/benchmark.md` |
| 6. Distribution | GitHub description and topics (`usage-based-billing`, `claude-code-plugin`, `codex-plugin`…) | | Marketplace and directory submissions; docs and SDK callouts; starter templates |

Tooling that already exists outside the repository:

- `claude plugin eval` (Claude Code 2.1.304) runs `case.yaml` suites with a `tool_used: Skill` grader and a with/without-plugin ablation arm. That covers the WS1 hit rate and the WS5 comparison for Claude Code without a custom harness.
- Codex has no equivalent command (`RELEASING.md` step 3). A Codex hit rate needs a scripted `codex exec` loop.
- The Lago MCP server source ([lago-agent-toolkit](https://github.com/getlago/lago-agent-toolkit)) exposes `create_billable_metric`, `create_plan`, `create_customer`, `create_subscription`, `create_event` and `preview_invoice`. The README lists 36 tools and omits `preview_invoice`. The Lago MCP connector failed to connect (503) in this audit session, so none of this was exercised.

## 5. Conflicts that need a decision

1. **WS4 against the demo invariant.** `SKILL.md:126`, `references/demo.md`, `references/cloud.md` and `references/safety.md` say Lago has no built-in sandbox and demo data must never go into Lago Cloud, "including a development, test, or staging account". `validate_repo.py` and the unit tests enforce those strings. The brief's WS4 seeds Atlas AI objects with "an API key", which breaks the rule on Cloud. Options:
   - (a) Self-hosted only: the script refuses any target that fails `validate_demo_target.py`. This is compliant today.
   - (b) Lago provides a real disposable sandbox or trial org, and the invariant is amended through an architecture decision.
   - (c) Seed on the user's own Cloud account. This needs a policy change and loosens a release-gated rule.

   Recommendation: (a) now, (b) as a request to the Lago team.
2. **Architecture-change rule.** CONTRIBUTING.md: "Do not add MCP, telemetry, runtime credentials, production actions, internal Lago material, or a new skill without an accepted architecture change." WS1 sub-skills and WS4 (MCP path, API key) each need an entry in `docs/architecture.md` in their PR.
3. **Vendor rule.** `references/vendor-positioning.md`: "No named alternative vendors are approved in this release." Trigger wording and `llms.txt` can name Stripe Billing and Chargebee only as migration sources, which are already supported. They can't be comparisons.
4. **"The 100 evals must still pass."** They have never been recorded as run. Options: score a sampled subset by hand on each branch, or convert the highest-risk cases (safety, approvals, demo isolation) to `claude plugin eval` graders as part of WS5. Recommendation: convert the safety subset first and treat the full manual run as a release gate, as `RELEASING.md` already does.
5. **Release integrity scans everything.** `release_integrity.py:12` ignores only `.git`, `.pytest_cache`, `.venv` and `__pycache__`. `packages/init/node_modules` and eval `results/` directories would fail the check. WS1 and WS3 must extend `IGNORED_PARTS` and `.gitignore`.
6. **Package name.** `@getlago/init` is free on npm and the `@getlago` org exists. `create-lago` is squatted. Lago already ships a Go `lago` CLI through Homebrew, so the init package must not claim the `lago` binary name.

## 6. Proposed sequencing

1. `fix/release-manifest-llms`: review the `llms.txt` change from PR #10, regenerate the manifest, get CI green.
2. WS1 triggers: measure first, it's the cheapest lever.
3. WS3 `START_HERE.md`, `llms.txt`, `packages/init`: the no-install path and the correct-code path.
4. WS2 multi-agent: mostly generation once WS1 and WS3 settle the content.
5. WS5 benchmark.
6. WS4 live step, after the section 5 decision.
7. WS6 distribution plan.

## Appendix: current agent formats

Checked against official docs on 2026-10-19. The most portable target is `.agents/skills/<name>/SKILL.md` with only the Agent Skills spec fields. Codex, Cursor, Copilot, Gemini CLI, Windsurf/Devin, Amp, OpenCode and Goose read that path.

**Spec limits** ([agentskills.io/specification](https://agentskills.io/specification)):

- `name`: 1–64 characters, lowercase, must match the folder name.
- `description`: 1–1024 characters.
- Optional fields: `license`, `compatibility`, `metadata`, `allowed-tools`.
- The current description is under the limit. The rewrite must stay under it.

| Agent | Project paths read | Other context | Distribution | Source |
| --- | --- | --- | --- | --- |
| Claude Code | `.claude/skills/`, plugin `skills/` | `CLAUDE.md` | Own marketplace; Anthropic directory via claude.ai/directory/manage | [skills](https://code.claude.com/docs/en/skills), [publish](https://code.claude.com/docs/en/plugins/publish) |
| Codex | `.agents/skills` | `AGENTS.md` (32 KiB cap) | `.agents/plugins/marketplace.json`; OpenAI plugin directory | [skills](https://learn.chatgpt.com/docs/build-skills), [submission](https://developers.openai.com/plugins/deploy/submission) |
| Cursor | `.agents/skills`, `.cursor/skills`, `.claude/skills` | `.cursor/rules/*.mdc`, `AGENTS.md` | Cursor marketplace, manual review | [skills](https://cursor.com/docs/context/skills), [plugins](https://cursor.com/docs/plugins) |
| GitHub Copilot | `.github/skills`, `.agents/skills`, `.claude/skills` | `.github/copilot-instructions.md`, `AGENTS.md` | `gh skill` | [skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) |
| Gemini CLI | `.gemini/skills`, `.agents/skills`, extension `skills/` | `GEMINI.md`, `gemini-extension.json` | Gallery crawls public repos with topic `gemini-cli-extension` | [skills](https://geminicli.com/docs/cli/skills/), [releasing](https://geminicli.com/docs/extensions/releasing/) |
| Windsurf / Devin Desktop | `.devin/skills`, `.windsurf/skills`, `.agents/skills` | `AGENTS.md` | n/a | [skills](https://docs.devin.ai/desktop/cascade/skills) |
| Cline | `.cline/skills`, `.clinerules/skills`, `.claude/skills` (not `.agents/skills`) | n/a | n/a | [skills](https://docs.cline.bot/features/skills) |
| Amp | `.agents/skills`, `.claude/skills` | n/a | `amp skill add` | [skills](https://ampcode.com/docs/customize/skills) |
| OpenCode | `.opencode/skills`, `.agents/skills`, `.claude/skills` | n/a | n/a | [skills](https://opencode.ai/docs/skills/) |
| Kiro | `.kiro/skills` | n/a | n/a | [skills](https://kiro.dev/docs/skills/) |

Skills directories:

- [skills.sh](https://skills.sh/docs) installs with `npx skills add owner/repo` and ranks by install telemetry. There is no submission step.
- The Gemini CLI gallery needs a root `gemini-extension.json` and the `gemini-cli-extension` topic.

Unverified or changing:

- Google moved unpaid Gemini CLI users to Antigravity CLI on 2026-06-18. Its file formats are not yet documented ([announcement](https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli)).
- Several rows came from summarized page fetches. WS2 re-checks each path against the raw page before generating files.
- Zed, Aider and Roo were not verified.

Lago facts for WS3 and WS4:

- **Invoice preview:** `POST /api/v1/invoices/preview` ([ref](https://getlago.com/docs/api-reference/invoices/preview)).
- **Webhook signatures:** JWT RS256 by default, with the public key from `GET /api/v1/webhooks/public_key`. HMAC-SHA256 is opt-in. Deduplicate on `X-Lago-Unique-Key` ([ref](https://getlago.com/docs/api-reference/webhooks/format---signature)).
