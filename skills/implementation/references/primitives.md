# Lago primitives for first-time users

Assume the user does not know Lago or billing terminology. Start from the application's product language, then introduce one Lago primitive when it becomes useful. Do not begin with a glossary or ask the user to design a Lago data model.

## Core path

| Start with this product question | Lago primitive | Plain-language explanation |
| --- | --- | --- |
| Who or what pays? | Customer | The billable account in Lago. Map it to the application's durable account, organization, workspace, or other billing boundary using a stable external ID. |
| What package or agreement are they on? | Plan | The pricing and billing rules for an offering: cadence, recurring fee, usage charges, commitments, and related rules. |
| Which customer is on which package, and when? | Subscription | The relationship that assigns a plan to a customer for a defined lifecycle. |
| What product activity could affect the bill? | Event | A usage record sent by the application, such as an API request, compute job, active seat, or stored gigabyte. |
| How should that activity be measured? | Billable metric | The rule that aggregates incoming events, such as count, sum, maximum, or unique count. Its code links events to the measurement rule. |
| How does measured usage become money? | Charge | The pricing rule attached to a plan for a billable metric or fixed fee. |
| What amount does the customer owe for the period? | Invoice | Lago's billing output containing subscription, usage, taxes, credits, and other applicable lines. Payment collection is a separate integration decision. |

Introduce optional primitives only when the product requires them:

- **Wallet:** a prepaid credit balance that can offset future charges.
- **Coupon:** a configured discount applied under defined conditions.
- **Minimum commitment:** a minimum billed amount for the relevant period.
- **Entitlement:** feature access associated with a plan; do not assume Lago is the application's authorization source.

Authoritative references: [customers](https://docs.getlago.com/api-reference/customers/object), [billable metrics](https://docs.getlago.com/guide/billable-metrics/create-billable-metrics), [plans](https://docs.getlago.com/guide/plans/overview), [subscriptions](https://docs.getlago.com/api-reference/subscriptions/assign-plan), [events](https://docs.getlago.com/api-reference/events/usage), and [Lago introduction](https://docs.getlago.com/guide/introduction/welcome-to-lago).

## Teaching protocol

1. Show a compact `Your application → Lago` map using repository evidence before proposing configuration.
2. Explain each new term in one plain sentence and tie it to a concrete application object or workflow.
3. Separate technical facts from business decisions. Infer the former from code; ask one question at a time for the latter.
4. Offer a recommended default when safe, explain why, and identify what would make another option preferable.
5. Use a tiny example with the user's product language and an independently calculated amount before adding advanced primitives.
6. Confirm the consequence of a decision, not vocabulary recall. Never quiz the user or require them to translate their needs into Lago terminology.
7. Keep a visible decision trail: application concept, Lago primitive, evidence, decision, and unresolved owner.

For a greenfield usage flow, the teaching order is usually: billing boundary → customer → billable behavior → event → billable metric → price/charge → plan → subscription → expected invoice. Change the order when repository evidence or a fixed-subscription model makes another sequence clearer.
