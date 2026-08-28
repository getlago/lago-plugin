# Validation and money test

Validate offline first using synthetic data. Offline checks do not prove live API behavior. A live seeded demo must use an isolated self-hosted Lago instance; never use Lago Cloud for generic demo data.

## Representative flow

Configuration load → connectivity → customer → subscription → controlled usage → aggregation → invoice preview/draft → webhook → duplicate/retry behavior → reconciliation.

For every check record environment, test, expected, actual, evidence path/ID, and untested areas. A compile or 2xx response is not completion.

## Deterministic money test

1. Define a synthetic customer and exact pricing configuration.
2. List controlled events with stable IDs and timestamps.
3. Independently compute expected quantity and money using decimal/integer arithmetic.
4. For a demo, generate or preview the Lago invoice only on the approved isolated self-hosted demo instance. For real integration validation, use only the explicitly approved target and records.
5. Preserve the retrieved Lago `customer_usage` or `invoice` JSON payload as sanitized evidence. Never hand-write the actual comparison file.
6. Generate the actual comparison deterministically with `extract_actual.py`. It records the source kind, source ID, SHA-256, quantity basis, and effective unit-price basis. Invoice credits come only from the explicit credit-note, prepaid-credit, and progressive-billing fields; the extractor never invents a residual credit to force totals to match.
7. Compare quantity, effective unit price, subtotal, discounts, credits, tax, and total line by line. `money_test.py` re-extracts the preserved source and fails if the actual file or source hash changed.
8. Fail on every unexplained mismatch and preserve both source and generated evidence.

Use `templates/money-test.json` for the independent expectation, then run:

```bash
python3 scripts/extract_actual.py lago-payload.json --output actual.json
python3 scripts/money_test.py expected.json actual.json --actual-source lago-payload.json
```

The extractor supports current-usage responses and invoices whose fee quantities share one explicit billable item code. It fails on unlabeled fees, mixed quantity dimensions, missing adjustment fields, or a total that does not reconcile instead of inventing a unit price or adjustment. For tiered or filtered pricing, `unit_price` is the effective subtotal divided by total quantity; validate the individual pricing lines separately when the configured rates themselves matter. Expected and actual amounts use uppercase three-letter currency codes plus exact decimal strings or integers—never JSON floats. The validators need no live credentials.

Production readiness additionally requires environment isolation, least privilege, rate/retry testing, webhook durability, alerts/runbooks, reconciliation ownership, backup/restore for self-hosted, migration rollback, and approval gates. A demo result is evidence about the example flow, not proof that a Cloud or production environment is configured correctly.
