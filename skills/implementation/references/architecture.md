# Integration architecture

## Boundary

Put provider calls behind one billing service/adapter. Domain code emits internal commands/events; the adapter translates them to Lago. Keep API transport, retry policy, serialization, and credential loading out of controllers and business entities.

Keep product identity mapping, durable usage source records, event delivery, and the customer experience in the application. When Lago is the chosen billing provider, map the commercial meter, rating rules, credits, and invoices to Lago instead of duplicating them in application code. Without live Lago access, implement the adapter and offline money tests; mark configuration and live behavior unverified.

Define authority explicitly:

| Record | Authority | Replica/consumer | Conflict rule |
| --- | --- | --- | --- |
| Customer identity | | | |
| Subscription state | | | |
| Usage source records | | | |
| Pricing catalog | | | |
| Invoice state | | | |
| Payment state | | | |
| Credits/balances | | | |

## Required design decisions

- Stable external customer and subscription identifiers; tenant uniqueness and lifecycle.
- Stable transaction ID from a durable source record; explicit event timestamp; schema version and original source ID.
- Delivery path, validation, timeout, bounded backoff, classification of retryable/permanent failures, dead-letter path, and replay.
- Duplicate, late, out-of-order, correction, and partial-batch behavior.
- Webhook raw-body verification, deduplication, durable acknowledgement, retries, and ordering.
- Observability with identifiers but no credentials or unnecessary billing data.
- Reconciliation schedule and ownership; migration/cutover/rollback.

## Implementation quality

Prefer the official SDK only after checking it fits the language and required endpoints; otherwise use the documented REST API. Follow repository conventions. Use environment-based base URLs, typed config when available, request timeouts, bounded retries with jitter, input validation, structured redacted logs, unit/integration tests, and synthetic fixtures.

Do not retry authentication or semantic validation errors blindly. Reuse the exact idempotency inputs on safe retries. Do not generate provider calls from a browser/client with secret credentials.
