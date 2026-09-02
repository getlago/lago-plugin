# Usage-event contract

## Canonical event

| Field | Rule |
| --- | --- |
| `code` | Stable contract matching a configured billable metric |
| `transaction_id` | Deterministic from a durable source record; never random per retry |
| `external_subscription_id` | Stable application subscription or billing-enrollment identifier; never substitute the customer ID merely because no subscription table exists |
| `timestamp` | Explicit occurrence time; retain unchanged on retries |
| value/properties | Numeric type and dimensions required by aggregation/pricing |
| source/schema version/original ID | Preserve lineage for replay and reconciliation |

Validate required keys, types, finite numeric values, allowed dimensions, tenant association, non-negative Unix timestamps, and schema version before enqueue/send. Apply a narrower past/future window only when the product's event contract defines one. Store delivery status separately from the source usage record.

Keep the customer identity and subscription identity distinct. If the application has no subscription entity yet, add a durable billing-enrollment or subscription-binding record that links the billable account to its Lago plan/subscription and lifecycle. Do not reuse the customer external ID as the subscription external ID unless the application already has an explicit, documented one-subscription-per-customer identity contract.

Run `validate_event.py` with `--numeric-property <name>` for custom aggregation fields. The common fields `amount`, `quantity`, `tokens`, `units`, and `value` are numeric by default. They must be finite numbers and non-negative. Use `--allow-negative-property <name>` only when the reviewed event contract and target event-store correction mechanism explicitly permit negative corrections.

## Delivery cases

- Duplicate: resend the identical stable key and timestamp; verify no added quantity.
- Retry: classify timeout/429/transient 5xx; bounded exponential backoff with jitter.
- Late/out-of-order: define billing-period and finalized-invoice consequences.
- Correction: preserve the original record and use the documented event-store-specific mechanism. Postgres and ClickHouse behavior differs.
- Replay: select by checkpoint; preserve IDs and timestamps; make restartable.
- Batch: record item-level results; never mark the whole batch delivered after partial failure.

For Lago's ClickHouse pipeline, uniqueness uses `transaction_id` plus `timestamp`; a retry with an omitted or changed timestamp can bill twice. Verify the target pipeline before asserting correction behavior.

Sources: [ingesting usage](https://docs.getlago.com/guide/events/ingesting-usage), [event API](https://docs.getlago.com/api-reference/events/event-object), [OpenAPI](https://swagger.getlago.com/openapi.yaml).
