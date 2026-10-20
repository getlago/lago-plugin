# Billing-correctness benchmark

Does a coding agent write correct usage-based billing code with Lago, and does this plugin change that? The benchmark gives the same task to the same agent twice, once with the plugin and once without any plugin. It then scores the finished code on behavior, not on wording.

This repository publishes the method and the tooling so anyone can reproduce or extend it. It does not publish results. The runner writes only to a directory you choose outside the repository, and a test fails if a result file is ever committed.

## Task

`evals/benchmark/tasks/python-usage-billing` scaffolds a small Python app with no billing. It uses only the standard library and SQLite, and one action records an LLM generation with input and output tokens. The prompt asks the agent to add Lago billing for a $49 monthly plan plus $0.02 per 1,000 tokens. It names a minimal module contract so the scorer can call the code:

- `setup_catalog()`
- `activate_billing(workspace_id)`
- `record_usage(generation_id)`
- `flush_usage()`
- `handle_lago_webhook(raw_body, headers) -> status`

The prompt describes the pricing and environment only. It does not mention idempotency, retries, duplicates, or signature checks; those are what the benchmark measures.

## Scenario and criteria

`evals/benchmark/checks/score.py` copies the finished workspace and runs its `billing.py` in a child process with a clean environment against a local fake of the Lago API (`checks/fake_lago.py`). The fake follows the required fields of the [Lago OpenAPI](https://swagger.getlago.com/openapi.yaml) and the documented duplicate-event behavior.

The scenario:
1. Creates the catalog and activates billing for one workspace.
2. Records two generations totalling 120,000 tokens. The first event delivery fails with HTTP 503.
3. Flushes, replays one generation, and flushes again. Then it keeps calling `flush_usage()` once a second for up to 90 seconds, like a worker would, so solutions that back off before retrying are not penalized.
4. Sends five webhooks.

| Criterion | Passes when |
| --- | --- |
| Idempotent events | Every event has an explicit timestamp. Retries reuse the same `transaction_id` and timestamp. The failed delivery is retried, not dropped or re-sent under a new ID. |
| No double billing | After the replay, stored usage is exactly 120,000 tokens. The subscription has its own ID, distinct from the customer's. |
| Correct charges | The plan is $49.00 USD monthly, its usage charge prices 120,000 tokens at $2.40 under any supported charge model, and stored events reach that metric with its aggregation field. |
| Webhook verification | A valid HMAC webhook and its replay return 2xx. A tampered body, a wrong key, and a missing signature return 4xx. |

### The scorer is tested

`tests/test_benchmark.py` runs the scorer on:
- a reference solution, which must pass all four criteria;
- six targeted defects, each of which must fail exactly its own criterion and nothing else:
  - a transaction ID minted per attempt;
  - a send-time timestamp;
  - a replay creating a new event;
  - a subscription reusing the customer ID;
  - a per-token price off by 1,000×;
  - a missing webhook signature check;
- a correct variant that backs off before retrying, which must pass every criterion;
- a module that fails to import, which must fail every criterion.

## Run it

Requirements: Claude Code with `claude plugin eval`, Python 3.9 or later, and `bash`.

```bash
python3 evals/benchmark/run_benchmark.py --out "$TMPDIR/lago-benchmark" --runs 3
```

The runner calls `claude plugin eval` with a with-plugin and a no-plugin arm. Each run gets a fresh HOME and configuration. The runner:
- always passes `--no-publish`, so no report is uploaded;
- copies each finished workspace out of the harness's sealed temporary directory, scores it, and deletes the temporary directory;
- drops spend fields from everything it writes;
- records the source commit and whether the tree was dirty or changed during the run, plus the Claude Code version, the observed model, and hashes of the runner, scorer, and task.

A run whose workspace or scenario result is missing counts as an error, never as a pass or a fail. The report is complete only when every planned run was scored from a clean tree.

## Reading results

A result is meaningful only with its provenance and coverage. Compare arms from the same report: same source commit, same model, same number of runs. Small run counts carry wide uncertainty.

Template for reporting a run. The repository intentionally ships it empty.

| Arm | Runs planned | Runs scored | Errors | Idempotent events | No double billing | Correct charges | Webhook verification | All four |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| With plugin | | | | | | | | |
| Without plugin | | | | | | | | |

Provenance: source commit, clean tree, Claude Code version, model, runner, scorer and task hashes.

## Limits

- **One task, one language, one agent.** Other agents and languages need their own runners.
- **A fake, not a real Lago.** The scorer judges what a fake Lago receives. It checks the integration contract, not a live invoice.
- **Partial webhook coverage.** Webhook processing beyond verification, acknowledgment, and duplicate acknowledgment is not scored.
- **A fixed contract.** The module contract makes scoring possible but is more specific than a typical request.
