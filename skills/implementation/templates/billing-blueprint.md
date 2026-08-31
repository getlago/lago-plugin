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

## Build now

- Smallest repository-consistent slice:
- Offline proof and tests:
- Explicitly out of scope:

## Decision needed next

Ask one question only if its answer changes architecture, billing behavior, or authorization. Include the recommended default and why.
