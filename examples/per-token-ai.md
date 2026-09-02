# OpenAI-style per-token demo

This is the canonical Lago Solution Engineer demo, adapted from Lago's [per-token pricing template](https://doc.getlago.com/templates/per-token/openai). Its bundled walkthrough runs entirely offline; optional live validation runs only on a dedicated isolated self-hosted Lago instance. The model names and prices are illustrative, not current OpenAI pricing. The walkthrough starts with a customer asking an AI research assistant to analyze a report, then shows that action becoming an explainable billing result before introducing Lago terminology.

Run the instant walkthrough with `python3 skills/implementation/scripts/run_demo.py`. The user does not need to configure anything, provide credentials, or modify a workspace.

## What it teaches

| Product concept | Lago primitive | Demo value |
| --- | --- | --- |
| AI Studio account | Customer | `demo_ai_studio` |
| Tokens consumed | Billable metric | `demo_ai_tokens`, summed from the `tokens` event property |
| Model and direction | Metric filters | `model`: `demo-small` or `demo-large`; `type`: `input` or `output` |
| Per-token package prices | Charges | Illustrative price per 1,000 tokens for each filter combination |
| Pay-as-you-go offer | Plan | `demo_per_token`, monthly, zero base fee |
| AI Studio on the offer | Subscription | `demo_ai_studio_per_token` |

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

## Illustrative prepaid result

After proving the `$0.37` gross usage charge, show one adjacent use case without changing the underlying usage signal. If Acme has an eligible `$10.00` USD prepaid wallet, no tax applies, and the invoice is finalized, Lago can apply `$0.37` of prepaid credits: the invoiced wallet balance becomes `$9.63` and the amount due becomes `$0.00`.

This does not simulate purchasing credits or collecting payment. Do not describe `$9.63` as a synchronous authorization balance: Lago applies wallet credits to eligible invoices, and real-time ongoing balance is an edition-dependent estimate. The application still owns access enforcement; payment, tax, and accounting remain separate decisions.

## Why the demo matters

- Engineering sends durable usage records instead of rebuilding aggregation, pricing, retry protection, credit application, and invoice calculation in product code.
- Product can use the same usage signal as a foundation for pay-as-you-go, prepaid, or hybrid packaging.
- Finance gets a line-by-line calculation that can be independently checked and reconciled.

## Evidence and stopping point

Retrieve current usage and compare each filtered charge with the independent $0.37 calculation. Retrieve a draft or preview invoice only if the selected self-hosted edition supports it; otherwise stop at current usage and label invoice generation unverified. Do not configure payments, tax providers, email delivery, or external webhooks.

Record the self-hosted Lago version, local base URL, created object IDs, event IDs, expected calculation, actual usage, and teardown target. Remove only the dedicated demo containers and volumes, and only after explicit approval.
