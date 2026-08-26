# Usage-event contract

## Canonical event

| Field | Rule |
| --- | --- |
| `code` | Stable contract matching a configured billable metric |
| `transaction_id` | Deterministic from a durable source record; never random per retry |
| `external_subscription_id` | Stable application subscription identifier |
| `timestamp` | Explicit occurrence time; retain unchanged on retries |
| value/properties | Numeric type and dimensions required by aggregation/pricing |
| source/schema version/original ID | Preserve lineage for replay and reconciliation |

Validate required keys, types, finite numeric values, allowed dimensions, tenant association, timestamp range, and schema version before enqueue/send. Store delivery status separately from the source usage record.

## Delivery cases

- Duplicate: resend the identical stable key and timestamp; verify no added quantity.
- Retry: classify timeout/429/transient 5xx; bounded exponential backoff with jitter.
- Late/out-of-order: define billing-period and finalized-invoice consequences.
- Correction: preserve the original record and use the documented event-store-specific mechanism. Postgres and ClickHouse behavior differs.
- Replay: select by checkpoint; preserve IDs and timestamps; make restartable.
- Batch: record item-level results; never mark the whole batch delivered after partial failure.

For Lago's ClickHouse pipeline, uniqueness uses `transaction_id` plus `timestamp`; a retry with an omitted or changed timestamp can bill twice. Verify the target pipeline before asserting correction behavior.

Sources: [ingesting usage](https://docs.getlago.com/guide/events/ingesting-usage), [event API](https://docs.getlago.com/api-reference/events/event-object), [OpenAPI](https://swagger.getlago.com/openapi.yaml).
