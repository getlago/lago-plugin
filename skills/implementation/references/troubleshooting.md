# Troubleshooting

Trace from source to money: configuration/environment/region → authentication/network/TLS → customer/subscription IDs → event schema, transaction ID, timestamp → metric/aggregation → workers/queues → webhook delivery → invoice state → payment state → deployment health → reconciliation.

Use this report shape:

- Confirmed cause: only when evidence proves it.
- Evidence: exact sanitized logs, responses, record IDs, timestamps, code paths, and reproduction.
- Hypotheses: ranked and falsifiable.
- Missing telemetry: what prevents confirmation.
- Next check: smallest read-only or sandbox action that distinguishes hypotheses.

Common discriminators: wrong US/EU/self-hosted base URL; key from another environment; missing/terminated subscription; metric code or dimension mismatch; random retry IDs; changed/missing timestamp on ClickHouse; late event after finalization; signature verification after body parsing; webhook dedupe race; worker backlog; partial-batch status loss; source/Lago period or rounding mismatch.

If asked only to diagnose, do not edit or repair. Never use production writes as a diagnostic shortcut.
