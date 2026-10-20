# Production-readiness checklist

- [ ] Environment, region, and base URL are explicit and isolated
- [ ] Credentials use least privilege and existing secret management
- [ ] Customer/subscription identity and authority are documented
- [ ] Event IDs and timestamps are deterministic across retries
- [ ] Partial failure, replay, late events, and corrections are tested
- [ ] Webhook signature, dedupe, durable acceptance, and retry are tested
- [ ] Independent money test matches Lago draft/preview
- [ ] Read-only reconciliation has an owner and schedule
- [ ] Logs/metrics/alerts redact secrets and unnecessary billing data
- [ ] Rate limits, timeouts, bounded retries, and failure queues are tested
- [ ] Migration cutover prevents duplicate billing and has rollback
- [ ] Self-hosted backup restoration and version rollback are rehearsed, if applicable
- [ ] Tax, accounting, payment, and finalization decisions have human owners
- [ ] Exact production action has separate approval
