# Billing models

Translate commercial intent into an independently testable formula before configuring Lago.

| Model | Confirm | Test cases |
| --- | --- | --- |
| Subscription | cadence, proration/lifecycle, currency | start, renew, change, cancel |
| Usage | unit, aggregation, tiers/filters, period | zero, boundary, tier crossing, duplicate |
| Hybrid | fixed + usage timing | both lines and combined total |
| Prepaid/wallet | grant/purchase, drawdown, expiry, priority | funding, depletion, rollover/expiry |
| Minimum commitment | period, minimum, included usage, overage | below/at/above minimum |

For AI-native and unclear monetization models, use [use-case discovery](use-case-discovery.md) before choosing a formula. Distinguish the technical unit that is measured from the product unit the customer buys. A product credit may span several models or features only when its conversion is deterministic, auditable, and independently testable.

For prepaid models, test purchased funding and free grants separately. Cover one-time, recurring, and threshold top-ups; eligible charges; low balance; exact depletion; insufficient balance; rollover or expiry; refund or reversal; and duplicate usage. State that application access control, payment, tax, and accounting are separate ownership decisions.

Keep money as integer minor units or exact decimal types. Define rounding per line and invoice; never invent it. Treat tax, discounts, credits, invoice finalization, payment collection, revenue recognition, and accounting as separate decisions with named owners.

For multi-tenant systems, decide whether Lago customer/subscription identity maps to organization, workspace, account, project, or another billing boundary. Avoid a shared event namespace that can collide across tenants.

Use a decision ledger:

| Decision | Options | Evidence | Owner | Status |
| --- | --- | --- | --- | --- |

Sources: [Lago plans](https://docs.getlago.com/guide/plans), [billable metrics](https://docs.getlago.com/guide/billable-metrics), [wallets](https://docs.getlago.com/guide/wallet-and-prepaid-credits/overview), [commitments](https://docs.getlago.com/guide/plans/commitment).
