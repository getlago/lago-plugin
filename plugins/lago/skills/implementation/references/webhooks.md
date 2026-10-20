# Webhooks

1. Capture the raw request body before JSON parsing.
2. Verify the configured Lago signature algorithm using the documented key/secret. Use constant-time comparison for HMAC.
3. Reject invalid signatures without processing.
4. Deduplicate on `X-Lago-Unique-Key` with durable storage and a unique constraint.
5. Persist the accepted envelope and acknowledge with 2xx only after durable acceptance.
6. Process asynchronously where supported. Make handlers idempotent and resilient to duplicates, retries, and out-of-order delivery.
7. Log unique key, type, timestamps, and internal trace ID; redact signatures, secrets, and unnecessary payload data.

Test valid/invalid signatures, malformed bodies, duplicate keys, handler retry, out-of-order lifecycle events, and durable-acceptance failure. Never use a parsed/re-serialized body for signature verification.

Current Lago headers include `X-Lago-Signature`, `X-Lago-Signature-Algorithm`, and `X-Lago-Unique-Key`. Verify current behavior before implementation.

Source: [webhook format and signature](https://docs.getlago.com/api-reference/webhooks/format---signature).
