# Synthetic self-hosted example

For local evaluation, follow the current official Docker instructions and label the result non-production. For Kubernetes, inspect and pin the current official Helm chart, then define verified values for ingress/TLS, secrets, persistence, services/workers, health probes, requests/limits, monitoring, backups, restore exercise, migrations, upgrade, and rollback.

For a live seeded demo, use a dedicated version-pinned local instance with isolated container, project, port, network, and volume names. Confirm the API base URL is local/self-hosted before creating prefixed fake customers, plans, subscriptions, or usage. Never redirect the demo to Lago Cloud.

Do not copy environment variable or chart value names from this example; retrieve them from the selected release.
