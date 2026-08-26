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
5. Compare quantity, unit price, subtotal, discounts, credits, tax when applicable, and total line by line.
6. Fail on every unexplained mismatch and preserve sanitized evidence.

Use `templates/money-test.json` and run `python3 scripts/money_test.py expected.json actual.json`. The validator uses decimal strings; no live credentials are required.

Production readiness additionally requires environment isolation, least privilege, rate/retry testing, webhook durability, alerts/runbooks, reconciliation ownership, backup/restore for self-hosted, migration rollback, and approval gates. A demo result is evidence about the example flow, not proof that a Cloud or production environment is configured correctly.
