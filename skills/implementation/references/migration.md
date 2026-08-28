# Migration control plane

## Sequence

Inventory → authority decisions → object/behavior mapping → dry run → restartable import → reconciliation → parallel validation → cutover gates → rollback/read-only retention.

Every migration produces this ledger:

| Source object or behavior | Lago target | Transformation | Historical treatment | Validation | Status |
| --- | --- | --- | --- | --- | --- |

Status must be one of: direct mapping; mapping with transformation; application-owned replacement; history retained in source; unsupported; unresolved; business decision; finance decision; tax/accounting decision.

Map customers/IDs, products/prices/plans, subscriptions/lifecycle, metrics/events, invoices/credits/commitments/balances/payments, scheduled changes, discounts, tax, webhooks, dunning, and downstream reporting. State what will not migrate.

Migration tooling requirements: dry-run default, stable source keys, idempotent upserts where documented, durable checkpoints, bounded batches, item-level error journal, resumability, immutable audit record, count/amount reconciliation, and no credentials in output.

Never delete, rewrite, recreate, or silently reinterpret finalized financial history. Retain it read-only in the source unless a documented requirement and human accounting/tax review say otherwise. Prevent source and Lago invoice/event routing overlap by customer and billing period.

Do not cancel or terminate a source subscription merely because its Lago replacement exists. First prove the cohort/customer and billing-period boundary, switch event and invoice ownership exactly once, reconcile the representative cycle, record the rollback checkpoint, and obtain approval for the named source subscriptions immediately before cancellation. Keep source access read-only through the agreed audit and rollback window.
