# PR 23 live money evidence

A new isolated self-hosted Lago v1.55.0 instance finalized a USD 2.40 invoice for 120,000 tokens at USD 0.00002 per token. Replaying the same transaction ID and timestamp returned 422; current usage and the invoice remained 240 cents. Subscription activation preceded usage; a separate synthetic customer and subscription were used.

The image was already cached. The dedicated Docker network is internal, with no external integrations configured. Host loopback ports were published but were not reachable on this Docker Desktop internal network. Requests therefore ran on container loopback through `docker exec` into the exact named container; no existing deployment or Lago Cloud was contacted. This proves live billing, not host-port accessibility.

Seeding through final invoice took 2 seconds after startup. Total time to first invoice including setup was not measured. The manifest candidate at the time was 9b7ce803b14fb047baf69e955b5410cb5a97801b. This evidence does not replace behavioral scorecards or authorize publication.

The preserved invoice includes a zero-value subscription fee and the metered fee. The seven-field money helper intentionally rejects combining different fee codes, so its hash-linked comparison uses the preserved current-usage payload. The finalized invoice's total was independently asserted to equal the same 240 cents.

```bash
python3 plugins/lago/skills/implementation/scripts/money_test.py docs/release-evidence/pr23-live-2026-10-20/expected.json docs/release-evidence/pr23-live-2026-10-20/actual.json --actual-source docs/release-evidence/pr23-live-2026-10-20/lago-current-usage.json
```

All stored data is synthetic. Credentials were generated in process and are absent from these artifacts. The exact container, network and volume in metadata remain local; no broad cleanup was performed.
