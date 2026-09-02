# Demo environment and synthetic data

Lago has no built-in sandbox mode. Each Lago account is one environment. Never call a Lago Cloud account a sandbox.

## Hard boundary

All seeded demos and generic fake usage must target an isolated self-hosted Lago instance created for the demo. Never seed demo customers, plans, subscriptions, events, wallets, invoices, or other synthetic objects into Lago Cloud, including an account the user calls development, test, or staging.

Lago Cloud may be used only for explicitly approved validation of the user's real integration and real non-production configuration. That is integration validation, not a demo, and must not introduce generic demo data.

## Canonical demo

Use the [OpenAI-style per-token demo](../../../examples/per-token-ai.md) unless the user asks for another scenario or explicitly asks to apply the walkthrough to the open application. Never personalize a first-run demo from an incidental workspace. The demo is based on Lago's [per-token pricing template](https://doc.getlago.com/templates/per-token/openai), adapted for isolated self-hosted Lago.

For the instant offline experience, run `python3 scripts/run_demo.py` from the skill directory (or the equivalent resolved path). It uses only Python's standard library, writes no files, needs no credentials, and produces the canonical mapping, duplicate-event check, reconciliation result, and $0.37 money test. Use `--json` when machine-readable evidence is useful.

Treat all model names, usage, and prices as illustrative. Do not claim they are current OpenAI models or prices. Keep the billable metric `field_name` and event property consistent, use deterministic transaction IDs and timestamps, and independently calculate the expected amount before sending anything.

## Demo workflow

1. Run and show the offline example first. Begin by saying the user does not need to configure or do anything. Include the synthetic scenario, application-to-Lago mapping, exact pricing formula, controlled usage events, duplicate result, reconciliation result, and expected total. This requires no Docker, credentials, Lago account, or workspace mutation.
2. If the user wants a live demo, inspect whether Docker and Docker Compose are available. Explain that the demo will download and start self-hosted Lago containers, bind local ports, and create disposable local data. Ask for approval immediately before those actions.
3. Follow the current [official Docker instructions](https://docs.getlago.com/guide/lago-self-hosted/docker). Use a reviewed, pinned Lago release rather than `latest` for a reproducible demo.
4. Isolate the demo with a dedicated directory, Compose project/container names, ports, network, and volumes. Do not reuse an existing Lago deployment or touch unrelated Docker resources.
5. Before any synthetic write, run `python3 scripts/validate_demo_target.py <base-url> --compose-project <dedicated-project>`. It must resolve to an explicit loopback port and a dedicated `lago-plugin-demo-<suffix>` project name. Then inspect the approved Compose project's container/port mapping and trace the URL to that exact container. A passing URL check alone, a user assertion, or an environment label is insufficient. Refuse Lago Cloud, remote, proxy-only, reused, or untraceable targets.
6. Seed clearly prefixed synthetic objects derived from the user's product example, send deterministic fake usage events, retrieve current usage or a draft/preview when supported, and compare it line by line with the independent money test.
7. Report every created object ID and the exact local resources used. Never enable payment collection, external tax, email delivery, or production webhooks for a demo.
8. Offer teardown instructions. Stop containers or delete the dedicated demo data only after explicit approval for the exact project and volumes; never run broad Docker cleanup commands.

If Docker is unavailable or the user declines local containers, keep the demo offline. Generated fixtures, calculations, mocks, and application code remain useful, but label live Lago behavior unverified.

Call the result `offline example complete`, not `validated` or `production-ready`. After an isolated self-hosted run, call it `live self-hosted validation complete` and keep production readiness as a separate gate.

Official context: [self-hosted overview](https://docs.getlago.com/guide/lago-self-hosted/overview), [Docker setup](https://docs.getlago.com/guide/lago-self-hosted/docker), and [integration testing](https://docs.getlago.com/guide/integration-testing).
