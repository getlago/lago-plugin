# Lago Cloud

Confirm the region; do not infer it. Current documented base URLs are `https://api.getlago.com` for US and `https://api.eu.getlago.com` for EU. Keep the base URL configurable and do not append `/api/v1` twice.

Cloud implementation checklist:

- Explicit Lago Cloud account/environment and least-privilege API key stored through existing secret management. Lago accounts are single environments; do not describe one as a built-in sandbox.
- API URL and environment are explicit and startup validation prevents accidental cross-environment use.
- Customer, subscription, event, and webhook flows are implemented behind the billing adapter.
- Webhook endpoint uses a publicly reachable TLS URL, raw-body signature verification, deduplication, and observability.
- Offline synthetic money tests pass before live validation. Cloud validation uses only the user's real integration configuration and explicitly approved test records—not a generic seeded demo.

Never seed a demo or generic fake usage into Lago Cloud, including an account named development, test, or staging. Run live demos only on isolated self-hosted Lago. Do not generate Lago infrastructure for a Cloud integration itself. Separate Lago catalog/account configuration from application configuration. Credentials are required only for live connectivity, never for plugin loading or offline design.

Sources: [Lago API introduction](https://docs.getlago.com/api-reference/intro), [Lago Cloud](https://docs.getlago.com/guide/lago-cloud), [integration testing](https://docs.getlago.com/guide/integration-testing).
