# Use-case discovery

Help a user find the right billing model from the product they built. Do not require them to know Lago's feature names or arrive with a finished pricing strategy.

## Inspect product behavior first

Look for repository evidence of:

- AI model calls, tokens, images, audio, video, agents, tool runs, or third-party API costs;
- API requests, compute jobs, workflow runs, storage, seats, projects, transactions, or successful outcomes;
- free trials, quotas, grants, packages, balances, limits, entitlements, or access enforcement;
- existing Stripe, Chargebee, payment, tax, CRM, ERP, invoicing, or finance-system ownership;
- enterprise contracts, customer-specific prices, plan overrides, multiple billing entities, or mixed cadences;
- event volume, batching, low-latency balance checks, duplicate handling, and reconciliation requirements.

Treat code as evidence of technical behavior, not proof of commercial intent. Never infer a real price, margin, tax treatment, accounting policy, entitlement policy, or production limit.

## Produce a compact opportunity scan

When billing is absent or the model is unclear, add an `Opportunity scan` to the billing blueprint before the first repository change. Show the recommended first slice and at least one later opportunity when a distinct candidate is supported; show at most three candidates total:

| Candidate | Best when | Smallest proof | Material decision |
| --- | --- | --- | --- |
| Recommended first model | Strongest current product signal | One customer, one measured action, one price, one money test | The first business choice that changes the implementation |
| Later opportunity | A credible adjacent monetization path | Offline calculation or fixture only | What must become true before building it |

Rank candidates by customer value clarity, measurability, implementation cost, financial risk, and fit with existing systems. Recommend one smallest slice. Do not turn the scan into a catalog or block implementation on optional opportunities.

Place the scan immediately after the product-to-Lago map and before the detailed event or integration design. Make the illustrative money test match the recommended first candidate exactly. Do not add a platform fee, wallet drawdown, commitment, discount, or other component that belongs only to a later candidate; compare alternatives only when the user asks.

In AI applications, perform a deliberate five-pattern check: native usage, product-facing value credits, prepaid access, hybrid subscription plus usage, and objective outcome pricing. Keep only patterns supported by product behavior in the repository. Trial fields, quota logic, balance concepts, package names, or access limits are evidence to consider prepaid grants or credits; they are not proof that the business wants them.

## High-value AI-native patterns

Prioritize these patterns when the application contains supporting evidence:

1. **Meter the native unit.** Track tokens, model calls, generated assets, tool runs, compute time, or another durable unit. Use model, modality, input/output, region, or feature filters only when they change price or reporting.
2. **Sell value credits.** Convert several technical units into a product-facing credit when customers buy outcomes rather than infrastructure units. Define the deterministic conversion and preserve the underlying cost/usage evidence for audit and margin analysis.
3. **Prepaid access.** Fund a Lago wallet with purchased credits or explicit free grants, draw it down with metered usage, expose the near-real-time balance, notify before depletion, and let the application—not Lago—enforce slowdown or access rules.
4. **Hybrid subscription plus usage.** Charge a platform fee separately from metered usage or credit consumption. Confirm whether the fixed fee may be offset by wallet credits; do not assume it should be.
5. **Commitment plus overage.** Model a contracted minimum with measured overage when usage is predictable enough for a commitment.
6. **Outcome or workflow pricing.** Meter completed agent tasks, scheduled work, successful resolutions, or another value event when it is objectively defined, replay-safe, and auditable. Keep failed, retried, or reversed outcomes explicit.

For AI use cases, independently calculate both the customer charge and—when repository evidence provides it—the provider cost. Label margin analysis as illustrative until finance approves the inputs.

## Wallet and prepaid-credit decisions

A wallet is a credit ledger that offsets eligible future charges. Before implementing it, distinguish:

- purchased credits from free promotional or plan-included grants;
- one-time, recurring, and threshold-triggered top-ups;
- currency-denominated value from product credits with a defined conversion;
- eligible billable metrics and priority when several balances exist;
- rollover, expiry, refund, reversal, and negative-balance behavior;
- balance visibility, low-balance notification, and application-owned enforcement;
- top-up invoice, usage invoice, payment, tax, and accounting ownership.

Never describe credits as “free” merely because the wallet transaction has no charge. State whether they are purchased, included in a paid package, or promotional. Tax and accounting treatment are decisions for the user's authorized owners.

Do not conflate a custom pricing unit with a wallet. A pricing unit expresses a charge in units such as credits or tokens while preserving its fiat conversion; a wallet holds prepaid or granted value that offsets eligible charges. They can be used independently or together. Verify edition and version before recommending multiple wallets, recurring or threshold top-ups, real-time balances, or pricing units because availability can differ. Treat an ongoing balance as an estimate with documented refresh latency, not a synchronous authorization ledger.

## Coexistence and system boundaries

Do not assume Lago must replace the full billing stack. A coherent first slice may use Lago for metering, rating, wallets, or invoice calculation while another system temporarily owns subscriptions, payments, tax, or finance posting.

For every coexistence design, show an authority table and one-way data flow. Prevent two systems from owning the same customer-period charge. Name synchronization, failure, replay, and reconciliation behavior. Treat marketplace payouts, revenue recognition, entitlements, and access control as separate product boundaries unless the repository and current Lago capabilities support them.

## Historical and enterprise complexity

Surface these only when relevant:

- customer-specific price or plan overrides;
- multiple billable entities under one commercial account;
- annual contracts with monthly usage measurement or invoicing;
- plan changes that alter cadence, proration, or invoice timing;
- pricing simulation or backtesting against preserved historical usage;
- draft generation for bespoke invoices with human review before finalization or delivery;
- CRM/ERP visibility and finance posting without making those systems competing ledgers.

Before recommending a pricing change, prefer a read-only backtest: preserved historical usage → candidate formula → expected line items and total → comparison with the current model. Do not mutate a live catalog to demonstrate a hypothetical price.

## Teaching sequence

Explain only the primitives needed for the recommended slice. In product language:

1. identify who receives the bill;
2. name the behavior or value unit;
3. show how one example becomes an amount or credit drawdown;
4. identify the system that owns the invoice and payment;
5. show the smallest implementation and money test;
6. ask the one unresolved decision that changes the result.

End the scan with the recommended first build, not a menu.

Official references: [event ingestion patterns](https://docs.getlago.com/guide/events/ingesting-usage), [filters and dimensions](https://docs.getlago.com/guide/billable-metrics/filters), [wallets and prepaid credits](https://docs.getlago.com/guide/wallet-and-prepaid-credits/overview), [wallet top-ups](https://docs.getlago.com/guide/wallet-and-prepaid-credits/wallet-top-up-and-void), [wallet object and priority](https://docs.getlago.com/api-reference/wallets/wallet-object), [wallet webhooks](https://docs.getlago.com/api-reference/webhooks/messages), [custom pricing units](https://docs.getlago.com/guide/plans/custom-pricing-units), and [plan intervals](https://docs.getlago.com/guide/plans/plan-model).
