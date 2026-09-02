# OpenAI-style per-token demo

This is the canonical Lago Solution Engineer demo, adapted from Lago's [per-token pricing template](https://doc.getlago.com/templates/per-token/openai). Its bundled walkthrough runs entirely offline; optional live validation runs only on a dedicated isolated self-hosted Lago instance. The model names and prices are illustrative, not current OpenAI pricing. Atlas AI is the merchant using Lago, Acme Corp is Atlas's customer, and an Acme employee is the end user. The walkthrough shows why one product action creates a non-trivial metering problem before turning it into an explainable billing result.

Run the instant walkthrough with `python3 skills/implementation/scripts/run_demo.py`. The user does not need to configure anything, provide credentials, or modify a workspace.

## What it teaches

| Product concept | Lago primitive | Demo value |
| --- | --- | --- |
| Acme Corp | Customer | `acme_corp` |
| Tokens consumed | Billable metric | `demo_ai_tokens`, summed from the `tokens` event property |
| Model and direction | Metric filters | `model`: `demo-small` or `demo-large`; `type`: `input` or `output` |
| Per-token package prices | Charges | Illustrative price per 1,000 tokens for each filter combination |
| Atlas Pro | Plan | `atlas_pro`, `$99` monthly base fee plus metered usage |
| Acme on Atlas Pro | Subscription | `acme_atlas_pro` |
| `$10` included AI allowance | Recurring granted wallet | Restricted to the `demo_ai_tokens` charge; it must not offset the base fee |

## Illustrative prices

| Model | Input / 1,000 | Output / 1,000 |
| --- | ---: | ---: |
| `demo-small` | $0.01 | $0.03 |
| `demo-large` | $0.02 | $0.06 |

## Controlled usage

Send four events with stable transaction IDs and explicit timestamps:

| Event | Tokens | Expected amount |
| --- | ---: | ---: |
| `demo_evt_small_input` | 12,000 input tokens on `demo-small` | $0.12 |
| `demo_evt_small_output` | 3,000 output tokens on `demo-small` | $0.09 |
| `demo_evt_large_input` | 5,000 input tokens on `demo-large` | $0.10 |
| `demo_evt_large_output` | 1,000 output tokens on `demo-large` | $0.06 |
| **Total** | **21,000** | **$0.37** |

Resend one event with the identical transaction ID and timestamp, then verify that the aggregated quantity and amount do not increase.

## Illustrative subscription, included usage, and overage

Atlas Pro costs `$99` per month and includes `$10` of AI usage through a recurring granted wallet restricted to the token charge. Acme has already consumed `$9.80` this month. The new report-analysis job costs `$0.37`: Acme's remaining `$0.20` of included usage is consumed and `$0.17` becomes overage. The independently calculated target invoice total before tax is `$99.17`.

The `$10` is a granted wallet allowance, not purchased prepaid credit, and its charge restriction keeps it from offsetting the subscription fee. The offline script proves the arithmetic, not Lago invoice generation. The application still owns access enforcement; payment, tax, and accounting remain separate decisions.

## Why the demo matters

- Engineering sends durable usage records instead of rebuilding aggregation, pricing, retry protection, credit application, and invoice calculation in product code.
- Product can use the same usage signal as a foundation for pay-as-you-go, prepaid, or hybrid packaging.
- Finance gets a line-by-line calculation that can be independently checked and reconciled.

This is the simplest shape. Lago also supports tiered and volume pricing, prepaid wallets, commitments and overages, customer-specific pricing, multiple billing entities, and plan changes. Late, corrected, and high-volume event streams require integration-specific validation.

## Evidence and stopping point

The archived live self-hosted evidence currently proves the `$0.37` metering result only. To validate the complete hybrid story, configure the `$99` plan and charge-restricted recurring `$10` wallet grant, reproduce the prior `$9.80` eligible usage, retrieve the resulting draft or finalized invoice, and compare it with the independent `$99.17` calculation. Until that payload is preserved and passes `money_test.py`, label `$99.17` as the expected illustrative result—not a Lago-produced invoice. Do not configure payments, tax providers, email delivery, or external webhooks.

Record the self-hosted Lago version, local base URL, created object IDs, event IDs, expected calculation, actual usage, and teardown target. Remove only the dedicated demo containers and volumes, and only after explicit approval.
