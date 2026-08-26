# OpenAI-style per-token demo

This is the canonical Lago Billing Engineer demo, adapted from Lago's [per-token pricing template](https://doc.getlago.com/templates/per-token/openai). It runs only on a dedicated isolated self-hosted Lago instance. The model names and prices are illustrative, not current OpenAI pricing.

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

## Evidence and stopping point

Retrieve current usage and compare each filtered charge with the independent $0.37 calculation. Retrieve a draft or preview invoice only if the selected self-hosted edition supports it; otherwise stop at current usage and label invoice generation unverified. Do not configure payments, tax providers, email delivery, or external webhooks.

Record the self-hosted Lago version, local base URL, created object IDs, event IDs, expected calculation, actual usage, and teardown target. Remove only the dedicated demo containers and volumes, and only after explicit approval.
