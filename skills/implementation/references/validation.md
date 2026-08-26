# Validation and money test

Validate in the smallest safe environment using synthetic data. Offline checks do not prove live API behavior.

## Representative flow

Configuration load → connectivity → customer → subscription → controlled usage → aggregation → invoice preview/draft → webhook → duplicate/retry behavior → reconciliation.

For every check record environment, test, expected, actual, evidence path/ID, and untested areas. A compile or 2xx response is not completion.

## Deterministic money test

1. Define a synthetic customer and exact pricing configuration.
2. List controlled events with stable IDs and timestamps.
3. Independently compute expected quantity and money using decimal/integer arithmetic.
4. Generate or preview the Lago invoice in a sandbox when authorized.
5. Compare quantity, unit price, subtotal, discounts, credits, tax when applicable, and total line by line.
6. Fail on every unexplained mismatch and preserve sanitized evidence.

Use `templates/money-test.json` and run `python3 scripts/money_test.py expected.json actual.json`. The validator uses decimal strings; no live credentials are required.

Production readiness additionally requires environment isolation, least privilege, rate/retry testing, webhook durability, alerts/runbooks, reconciliation ownership, backup/restore for self-hosted, migration rollback, and approval gates.
