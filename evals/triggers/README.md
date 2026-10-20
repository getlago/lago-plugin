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

`--ablation none` is required: in a two-arm run, Skill graders are reported but not scored. Runs that hit the 4-turn cap count only when the expected activation grader completed. Other errors, absent graders and missing attempts are reported as incomplete; the summarizer exits nonzero. Rates use completed observations, and `coverage` exposes planned, completed and errored attempts.

Codex has no plugin eval command. `codex_triggers.py` installs this checkout as `lago@lago-plugins` into a temporary `CODEX_HOME`, the same path users take with `codex plugin add`. It copies only `auth.json` from your Codex home and deletes the temporary home afterwards. A run counts as loaded only after a completed, successful standalone `cat` of the exact installed skill path returns the full skill text. Shell-wrapped `cat` is supported. Other read forms, truncated output or failed attempts are unclassified errors, not misses or successful loads. This conservative observation method may require extending for future CLI read tools.

```bash
python3 evals/triggers/codex_triggers.py --runs 2 -j 3 > "$TMPDIR/codex-triggers.json"
```

Each Codex attempt records its outcome; successful reads include the command, exit code and content hash, without saving agent responses or credentials. Output includes CLI version, requested model, source commit, dirty state and skill hash. Pin `--model` for comparisons. Incomplete runs exit nonzero; rates alone must never be used without `coverage` and `complete`.

## Historical results

Claude Code 2.1.304, Codex CLI 0.163.0, measured 2026-10-19. The before column is the description on `main` at `9ce0119`.

| Agent | Measure | Before | After |
| --- | --- | ---: | ---: |
| Claude Code, 3 runs per prompt | Positive prompts that fired the skill | 86/96 (90%) | 95/96 (99%) |
| Claude Code, 3 runs per prompt | Near-misses that fired it (completed observations) | 2/42 | 0/43 |
| Claude Code | Incomplete negative attempts | 3/45 | 2/45 |

**Claude Code misses before:**
- "Add usage-based billing to this Next.js app"
- Express metered API calls
- tiered volume pricing
- credit wallets
- three migration prompts ("moving off Stripe Billing", "replace our Stripe usage records", "on Chargebee, add usage pricing")

**Claude Code after:** one run of "replace our Stripe usage records" still missed.

**False triggers before:**
- Claude Code: EU VAT, single-order receipt

Both historical evaluations are incomplete: the personal-expense-tracker case timed out three times before and twice after. The old summarizer incorrectly counted those timeouts as valid negatives. The corrected summarizer exits 1 for both archived files while reporting the usable observations.

These are small samples. Rerun after any description change and compare against this table.

The historical Codex numbers are withdrawn: the old runner accepted commands mentioning a skill path without proving a successful read. Its baseline also omitted one failed negative attempt. A new full before/after comparison is pending; no replacement improvement claim is made.

Sanitized original Claude grader artifacts are archived in [evidence/claude-before.json](evidence/claude-before.json) and [evidence/claude-after.json](evidence/claude-after.json). Reproduce the table with:

```bash
python3 evals/triggers/summarize.py evals/triggers/evidence/claude-before.json
python3 evals/triggers/summarize.py evals/triggers/evidence/claude-after.json
```

These preserve per-attempt graders, errors, timestamps and CLI version; ephemeral trace paths were removed and local checkout paths were replaced with `<checkout>`. The original artifacts did not capture model IDs or source hashes. The before revision above was reported by the original operator; an immutable after revision cannot be established from these files. These are historical observations, not a fully reproducible benchmark or evidence of integration correctness. Future comparisons must archive exact clean source commits, model IDs, CLI versions, commands and per-run observations for both arms.

## Corrected-runner smoke checks

At clean commit `4d9e081e41a1ee9346889936150f08aecdfe658a`, Codex CLI 0.163.0 loaded the skill for `seat-plus-usage` and did not load it for `eu-vat-calculation` (one attempt each, default model unpinned). [Positive evidence](evidence/codex-smoke-positive.json) and [negative evidence](evidence/codex-smoke-negative.json) record the source, runner and skill hashes, commands, timestamps and outcomes. The ephemeral home path is redacted. These check the runner against a live CLI; they are not a replacement benchmark.
