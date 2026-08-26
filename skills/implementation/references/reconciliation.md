# Reconciliation

Read-only by default. Compare the same customer, subscription, currency, and billing-period boundaries across sources.

| Layer | Source side | Lago side | Stable join |
| --- | --- | --- | --- |
| Customers | application accounts | Lago customers | external customer ID |
| Subscriptions | app lifecycle | Lago subscriptions | external subscription ID |
| Usage | durable source events | accepted events | transaction ID + timestamp where applicable |
| Aggregates | independent calculation | Lago usage/fees | metric, dimensions, period |
| Invoices | expected period/amount | draft/final invoice | external refs + period |
| Payments | provider/application | invoice payment state | provider/reference ID |

Classify each difference: missing in Lago; missing in source; identifier mismatch; state mismatch; amount mismatch; timing difference; expected eventual consistency; unresolved.

Normalize timestamps, currencies, decimal precision, and status vocabulary explicitly. Never hide differences behind a tolerance; document any approved rounding tolerance and still report raw values.

Output counts, totals, discrepancy rows, evidence, and recommended next check. Do not repair automatically. A repair plan names exact records, billing impact, approvals, and rollback.
