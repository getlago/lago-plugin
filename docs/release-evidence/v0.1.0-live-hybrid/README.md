# v0.1.0 live self-hosted hybrid money test

Run date: 2026-09-02

Result: **PASS**

The complete Atlas/Acme one-period example ran on a new loopback-only self-hosted Lago `v1.52.1` instance. The image was the pinned `getlago/lago:v1.52.1` digest `sha256:e0fa3a9bfdfeea607ac6fb8a24c010188451baf2358df351d18116a773c0a472`.

No Lago Cloud or company environment was contacted. All identifiers and data were synthetic. Payment collection, external tax, email delivery, PDF generation, and external webhooks were disabled or unused.

## Result

| Component | Lago result |
| --- | ---: |
| Subscription billed in advance | `$99.00` |
| Gross eligible usage | `$10.17` |
| Restricted granted-wallet credit | `-$10.00` |
| Usage overage billed in arrears | `$0.17` |
| Tax | `$0.00` |
| **Period total before tax** | **`$99.17`** |

Lago produced two finalized invoices because the subscription was billed in advance and usage in arrears. This proves the period total, not a promise of one consolidated invoice. The usage payload contained five accepted events: `$9.80` of prior usage and the four-event `$0.37` job. Replaying one job transaction returned HTTP `422` and did not increase usage.

The wallet was restricted to the AI billable metric, so none of its credit offset the `$99` subscription. This run proves a one-period grant and drawdown. It does not prove automatic monthly wallet renewal, which is edition-dependent and must be validated for the selected deployment.

## Preserved evidence

- `lago-current-usage.json`: Lago's usage response before invoicing.
- `lago-invoice-summary.json`: exact monetary fields from both Lago invoice responses.
- `result.json`: independently checked aggregate result.
- `run-metadata.json`: isolated target, pinned image, synthetic IDs, and disabled integrations.

The named test containers and volumes are intentionally preserved pending explicit teardown approval.
