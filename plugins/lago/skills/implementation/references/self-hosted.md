# Self-hosted Lago

Use only currently documented deployment paths and settings. Official starting points are Docker for local evaluation and the official Helm chart for Kubernetes. Docker Compose is not production-ready merely because it starts successfully.

## Environments

- Local evaluation: disposable data, documented sample configuration, no production claims.
- Staging: representative persistence, workers, ingress/TLS, backup/restore exercise, monitoring, upgrade rehearsal.
- Production: reviewed topology and capacity, secret management, persistent storage/object storage/email as required by the verified release, health/readiness/liveness, requests/limits, backups and restore testing, database migration plan, monitoring/alerts, scaling, upgrade and rollback.

Inspect the official release/chart for PostgreSQL, Redis, workers, scheduled jobs, ingress, storage, and every environment variable or Helm value. Do not invent names or copy values from an unrelated version. Pin versions; avoid `latest` in production artifacts.

Deployment evidence must include rendered/validated manifests or Compose config, health checks, migration outcome, backup/restore result, and a rollback rehearsal proportional to risk.

## Seeded demos

All live demos use a dedicated local self-hosted instance; never reuse an existing self-hosted deployment. Inspect Docker availability, pin the Lago release, isolate names/ports/networks/volumes, and get approval before pulling images or starting containers. Require the deterministic demo-target check plus evidence that the loopback port belongs to the exact approved Compose project. Read [demo environment](demo.md) before creating fake objects or usage.

Sources: [self-hosted overview](https://docs.getlago.com/guide/lago-self-hosted/overview), [Docker](https://docs.getlago.com/guide/lago-self-hosted/docker), [official Helm chart](https://github.com/getlago/lago-helm-charts).
