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

Validate required keys, types, finite numeric values, allowed dimensions, tenant association, non-negative Unix timestamps, and schema version before enqueue/send. Apply a narrower past/future window only when the product's event contract defines one. Check that the event's original occurrence time belongs to the intended subscription period. For new signup flows, activate billing before recording billable work; if the contract legitimately starts earlier, configure the effective start deliberately. Do not change an old event's timestamp merely to force it into a period. Store delivery status separately from the source usage record.

Keep the customer identity and subscription identity distinct. If the application has no subscription entity yet, add a durable billing-enrollment or subscription-binding record that links the billable account to its Lago plan/subscription and lifecycle. Do not reuse the customer external ID as the subscription external ID unless the application already has an explicit, documented one-subscription-per-customer identity contract.

Run `validate_event.py` with `--numeric-property <name>` for custom aggregation fields. The common fields `amount`, `quantity`, `tokens`, `units`, and `value` are numeric by default. They must be finite numbers and non-negative. Use `--allow-negative-property <name>` only when the reviewed event contract and target event-store correction mechanism explicitly permit negative corrections.

## Delivery cases

- Duplicate: resend the identical stable key and timestamp; verify no added quantity. A duplicate validation error is not a generic success response. Reconcile it against the original durable source record and the stored event's subscription, metric, timestamp, and properties before marking delivery complete. Do not treat every HTTP 422 as an accepted duplicate.
- Retry: classify timeout/429/transient 5xx; bounded exponential backoff with jitter.
- Late/out-of-order: define billing-period and finalized-invoice consequences.
- Correction: preserve the original record and use the documented event-store-specific mechanism. Postgres and ClickHouse behavior differs.
- Replay: select by checkpoint; preserve IDs and timestamps; make restartable.
- Batch: record item-level results; never mark the whole batch delivered after partial failure.

For Lago's ClickHouse pipeline, uniqueness uses `transaction_id` plus `timestamp`; a retry with an omitted or changed timestamp can bill twice. Verify the target pipeline before asserting correction behavior.

An ingestion 2xx means the event was accepted, not necessarily rated. Reconcile filtered event pages, current usage, and invoice fee units and amounts before claiming that a customer's usage was billed. In an isolated self-hosted v1.55.0 check, events timestamped to the whole second just before a newly created subscription's fractional start time were stored but absent from current usage. A separate check sent 7 and 5 analyzed pages after subscription activation; a plan with 10 included pages and 2¢ per overage page produced 12 usage units and a finalized 4¢ charge. Replaying the same event returned HTTP 422 with `transaction_id: value_already_exist` and added no unit. These are bounded local results, not a throughput, cloud, or late-correction guarantee.

When checking an apparent duplicate, use subscription- and period-filtered event results with pagination and compare the full source identity. Do not rely on an unqualified transaction-ID lookup where the same ID can exist on different subscriptions. If the stored event cannot be matched unambiguously, leave the delivery unresolved for investigation rather than silently dropping or rebilling it.

## Reconcile a metered invoice

For a finalized invoice, page through `GET /events` with `external_subscription_id`, the billable metric `code`, and the fee period's `timestamp_from`/`timestamp_to`. Compare distinct transaction IDs and original properties with the plan's aggregation and charge filters. Rebuild each filter bucket and the unmatched default-price bucket; stop for investigation if an event matches overlapping filters or cannot be assigned confidently. Compare each bucket's units, event count, and independently calculated amount with `current_usage` before finalization and the invoice's charge fees afterward. Reconcile credits, discounts, and tax separately from the usage fee.

This is a reconstruction from event and pricing data, not a native list of transaction IDs attached to each fee. In one isolated self-hosted v1.55.0 `count_agg` test, 17 stored events reconstructed three finalized fee lines: 10 `search/us` calls at 2¢, four `generate/eu` calls at 4¢, and three default-price calls at 1¢, for 39¢ total. The default-price line combined two different event-property combinations, so the invoice alone could not identify them. The check covers one synthetic period; do not generalize it to production throughput, late corrections, or a native per-event audit export.

Sources: [ingesting usage](https://docs.getlago.com/guide/events/ingesting-usage), [event API](https://docs.getlago.com/api-reference/events/event-object), [OpenAPI](https://swagger.getlago.com/openapi.yaml).
