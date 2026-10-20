---
tags: [benchmark]
allowed_tools: [Read, Glob, Grep, TodoWrite]
---

Add usage-based billing to this app with Lago.

Pricing: a Pro plan at $49 per month, plus $0.02 per 1,000 tokens. Tokens are input plus output tokens of each generation. Every workspace in this app is on Pro.

Environment: Lago is at `LAGO_API_URL` (API origin, without `/api/v1`) with the API key in `LAGO_API_KEY`. Our Lago webhook endpoint is configured with HMAC signatures, and the HMAC key is in `LAGO_WEBHOOK_HMAC_KEY`. You cannot reach a real Lago instance from here. Use only the Python standard library; no packages can be installed.

Our test harness will import a `billing.py` module at the repository root and call:

- `setup_catalog()`: create whatever Lago configuration the pricing needs.
- `activate_billing(workspace_id)`: start billing for an existing workspace.
- `record_usage(generation_id)`: called after a generation row is stored.
- `flush_usage()`: called periodically by a worker.
- `handle_lago_webhook(raw_body: bytes, headers: dict) -> int`: returns the HTTP status to send.

Keep the functions in `app/db.py` working.
