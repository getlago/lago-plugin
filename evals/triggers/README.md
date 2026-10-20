# Trigger evals

Does the `implementation` skill activate on the words developers actually use, even when they never say "Lago"? And does it stay quiet on near-misses?

- `positive/`: 32 prompts that should activate the skill. 30 never name Lago, for example "Add usage-based billing to this Next.js app", "charge per token", "prepaid credits", "seat plus usage" and "moving off Stripe Billing". Two control prompts do name Lago.
- `negative/`: 15 near-misses that should not activate it: one-off checkout, PayPal donations, VAT and sales tax, card storage, receipts, Stripe Connect payouts, API rate limiting, product analytics and an expense tracker.

Each case has one `tool_used` grader on the `Skill` tool. A positive passes when the skill is called. A negative passes when it is never called.

## Run

Claude Code (`claude plugin eval`, https://code.claude.com/docs/en/plugin-evals):

```bash
claude plugin eval . --eval-dir evals/triggers --ablation none --trust-plugin --no-publish \
  --threshold 0 -j 4 --json "$TMPDIR/triggers.json"
python3 evals/triggers/summarize.py "$TMPDIR/triggers.json"
```

`--ablation none` is required: in a two-arm run, Skill graders are reported but not scored. Runs that hit the 4-turn cap still carry grader results and are counted.

Codex has no plugin eval command. `codex_triggers.py` installs this checkout as `lago@lago-plugins` into a temporary `CODEX_HOME`, the same path users take with `codex plugin add`. It copies only `auth.json` from your Codex home and deletes the temporary home afterwards. A run counts as triggered when the agent reads the skill's `SKILL.md`.

```bash
python3 evals/triggers/codex_triggers.py --runs 2 -j 3
```

## Results

Claude Code 2.1.304, Codex CLI 0.163.0, measured 2026-10-19. The before column is the description on `main` at `9ce0119`.

| Agent | Measure | Before | After |
| --- | --- | ---: | ---: |
| Claude Code, 3 runs per prompt | Positive prompts that fired the skill | 86/96 (90%) | 95/96 (99%) |
| Claude Code, 3 runs per prompt | Near-misses that fired it | 2/45 | 0/45 |
| Codex, plugin installed, 2 runs per prompt | Positive prompts that fired the skill | 64/64 | 64/64 |
| Codex, plugin installed, 2 runs per prompt | Near-misses that fired it | 3/29 | 0/30 |

**Claude Code misses before:**
- "Add usage-based billing to this Next.js app"
- Express metered API calls
- tiered volume pricing
- credit wallets
- three migration prompts ("moving off Stripe Billing", "replace our Stripe usage records", "on Chargebee, add usage pricing")

**Claude Code after:** one run of "replace our Stripe usage records" still missed.

**False triggers before:**
- Claude Code: EU VAT, single-order receipt
- Codex: EU VAT, card storage

These are small samples. Rerun after any description change and compare against this table.
