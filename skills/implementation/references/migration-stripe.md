# Stripe Billing migration

Inspect customers, products, prices, subscriptions/items, meters/usage, credits, coupons/discounts, invoices/credit notes, payment methods/intents, tax, webhooks, schedules, trials, cancellations, and anchors. Use current Stripe docs and the detected API version; do not infer semantics from field names.

Stable mapping baseline:

- Stripe customer ID → Lago external customer ID
- Stripe subscription ID → Lago external subscription ID
- Stripe product/price ID → reviewed Lago plan/charge mapping
- Durable Stripe/source usage ID → Lago transaction ID
- Stripe invoice ID → reconciliation reference

Choose new-only, cohort/renewal-date, parallel, or full cutover based on risk. Retain finalized Stripe invoices, payments, credit notes, and audit history by default. Migrate remaining balances only after finance-approved semantics.

Cutover gates: catalog frozen/versioned; customer/subscription counts reconcile; event router has one owner per period; draft Lago money tests match independently calculated expectations; payment, tax, dunning, webhook, scheduled-change, and cancellation ownership are explicit; rollback can restore routing without duplicate billing.

Never cancel, modify, or query production Stripe without explicit approval immediately before the exact action. Cancellation is a post-cutover action: Lago object creation, a dry run, or draft parity is not sufficient. Require proven routing ownership, customer-period reconciliation, a recorded rollback checkpoint, and the exact Stripe subscription selector before seeking cancellation approval.

Sources: [Stripe Billing](https://docs.stripe.com/billing), [usage meters](https://docs.stripe.com/billing/subscriptions/usage-based), [credit grants](https://docs.stripe.com/api/billing/credit-grant), [API versions](https://docs.stripe.com/upgrades).
