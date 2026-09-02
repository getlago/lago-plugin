# Demo environment and synthetic data

Lago has no built-in sandbox mode. Each Lago account is one environment. Never call a Lago Cloud account a sandbox.

## Hard boundary

All seeded demos and generic fake usage must target an isolated self-hosted Lago instance created for the demo. Never seed demo customers, plans, subscriptions, events, wallets, invoices, or other synthetic objects into Lago Cloud, including an account the user calls development, test, or staging.

Lago Cloud may be used only for explicitly approved validation of the user's real integration and real non-production configuration. That is integration validation, not a demo, and must not introduce generic demo data.

## Canonical demo

Use the [OpenAI-style per-token demo](../../../examples/per-token-ai.md) unless the user asks for another scenario or explicitly asks to apply the walkthrough to the open application. Never personalize a first-run demo from an incidental workspace. The demo is based on Lago's [per-token pricing template](https://doc.getlago.com/templates/per-token/openai), adapted for isolated self-hosted Lago.

For the instant offline experience, run `python3 scripts/run_demo.py` from the skill directory (or the equivalent resolved path). It uses only Python's standard library, writes no files, and needs no credentials. Atlas AI is the merchant; Acme Corp is its customer; an Acme employee is the end user. Atlas Pro costs an illustrative `$99` per month and includes `$10` of AI usage. The walkthrough makes the metering problem visible, verifies a duplicate-safe `$0.37` job, consumes Acme's last `$0.20` of included usage, and calculates `$0.17` of overage and a `$99.17` invoice total before tax. Use `--json` when machine-readable evidence is useful.

Treat all model names, usage, and prices as illustrative. Do not claim they are current OpenAI models or prices. Keep the billable metric `field_name` and event property consistent, use deterministic transaction IDs and timestamps, and independently calculate the expected amount before sending anything.

## Demo workflow

1. Run and show the offline example first. Begin by saying the user does not need to configure or do anything. Identify the merchant, billed customer, end user, and pricing before making the transformation visible: product action → multiple durable usage records and retry → tenant attribution → metering → pricing → included-usage consumption → overage → invoice result. Include the exact pricing formula, controlled usage events, duplicate result, reconciliation result, gross charge, credit application, overage, and invoice total. State what the merchant avoids building and what remains outside Lago. Explain Lago primitives only after the outcome is clear. This requires no Docker, credentials, Lago account, or workspace mutation.

Treat the subscription, included usage, prior `$9.80` consumption, and tax-free result as illustrative. The included value is a plan allowance or grant, not purchased prepaid credit. It applies only to the metered AI usage, not the `$99` subscription. Payment collection, tax, accounting, and application access enforcement remain separate.

Keep the visible walkthrough to four compact beats: `Who sells what`, `One click, messy usage`, `Lago makes it billable`, and `The result`. Then name what the merchant avoids building and add one concise credibility line: Lago also supports tiered and volume pricing, prepaid wallets, commitments and overages, customer-specific pricing, multiple billing entities, and plan changes. Do not imply that the simple example proves late-event, correction, or high-volume behavior; those require integration-specific validation.
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
