---
type: llm
focus: trace
---
Judge the billing integration the agent wrote into the Next.js app. PASS only if all hold:
1. Each usage event's `transaction_id` comes from the stored generation record (for example `generation.id`), not a value created at send time, and a retry would reuse it with the same `timestamp`.
2. Events carry `external_subscription_id` from a subscription identifier distinct from the customer or workspace ID, or the agent adds a stored subscription ID.
3. A webhook route reads the raw body (`request.text()` or equivalent) before verifying `X-Lago-Signature` (JWT or HMAC), deduplicates on `X-Lago-Unique-Key`, and returns 2xx only after storing the webhook.
4. No API key or secret is hardcoded. Configuration comes from environment variables, and the region or base URL is not silently assumed.
5. A 422 duplicate response is not counted as a plain success.
6. Webhook acceptance writes retryable durable work atomically; it does not insert a dedupe key and then rely on a separate enqueue call.
7. Prepaid reads, if used, select currency and eligible charges across pages and are not presented as atomic spending authorization.
8. Subscription start and billing cadence are explicit; usage is not recorded before activation, and initial subscription fees are reconciled separately from current usage. Activation recovery handles second-precision `subscription_at` responses and checks inactive statuses before recreating an enrollment. Termination disables access through the verified webhook or an explicit-status lookup; an active-only 404 must not leave access enabled. Repeated creation after an ambiguous failure must not reactivate a terminated enrollment.
9. Authenticated requests refuse redirects, and transient non-JSON responses use bounded status-based retries.
FAIL if any item is missing or wrong. In the explanation, list which items failed.
