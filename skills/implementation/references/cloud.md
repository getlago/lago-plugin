# Lago Cloud

Confirm the region; do not infer it. Current documented base URLs are `https://api.getlago.com` for US and `https://api.eu.getlago.com` for EU. Keep the base URL configurable and do not append `/api/v1` twice.

Cloud implementation checklist:

- Sandbox/non-production workspace and least-privilege API key stored through existing secret management.
- API URL and environment are explicit and startup validation prevents accidental cross-environment use.
- Customer, subscription, event, and webhook flows are implemented behind the billing adapter.
- Webhook endpoint uses a publicly reachable TLS URL, raw-body signature verification, deduplication, and observability.
- Synthetic sandbox money test and reconciliation pass before any production proposal.

Do not generate Lago infrastructure for Cloud. Separate Lago catalog/workspace configuration from application configuration. Credentials are required only for live connectivity, never for plugin loading or offline design.

Sources: [Lago API introduction](https://docs.getlago.com/api-reference/intro), [Lago Cloud](https://docs.getlago.com/guide/lago-cloud).
