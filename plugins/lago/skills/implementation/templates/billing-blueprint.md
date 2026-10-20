# Billing blueprint

## Recommended outcome

One sentence in the product's language.

## Your application → Lago

| Product concept | Repository evidence | Lago role | Plain-language meaning |
| --- | --- | --- | --- |
| Who pays | | Customer | The account that receives the bill. |
| What they buy | | Plan + subscription | The pricing rules and the account using them. |
| What affects the bill | | Event + billable metric | Product activity and the rule that measures it. |
| How usage becomes money | | Charge | The price applied to measured activity. |

## Smallest working flow

`application action → usage record → measured quantity → price → expected amount`

Use an independently calculated, clearly illustrative amount until the user supplies approved pricing.

## Opportunity scan

Include this section only for a new or unclear billing model, before the first repository change. Show the recommended first slice and at least one later opportunity when repository evidence supports one; show at most three candidates total.

| Candidate | Repository signal | Why now or later | Smallest proof |
| --- | --- | --- | --- |
| Recommended | | | |
| Later opportunity | | | |

Do not infer commercial terms. Separate native usage units, product-facing credits, wallet funding, invoice ownership, payment ownership, and application-owned access enforcement. The money example must include only the recommended candidate's components.

## Build now

- Smallest repository-consistent slice:
- Offline proof and tests:
- Explicitly out of scope:

## Decision needed next

Ask one question only if its answer changes architecture, billing behavior, or authorization. Include the recommended default and why.
