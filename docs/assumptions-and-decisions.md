# Assumptions and unresolved decisions

## Assumptions

- Repository and future GitHub location: `getlago/lago-plugin`.
- Planned shareable plugin slug: `lago`; marketplace slug: `lago-plugins`; current version: `0.2.0`; license: MIT. This intentionally produces `lago@lago-plugins` and keeps the company-only marketplace identity out of a future public release.
- Python 3.9+ is supported for optional offline validators; skill loading has no runtime dependency.
- Lago's official docs and OpenAPI remain the authority for version-sensitive behavior.

## Decisions required before official marketplace submission

- Confirm Lago legal/brand approval for the plugin name, MIT license, and publisher metadata.
- Confirm the OpenAI and Anthropic publisher accounts and listing metadata. The repository is currently internal; publication and marketplace approval remain separate decisions.
- Decide the supported minimum Claude Code and Codex versions after clean-machine testing.
- Completed: the authorized usage-only and full one-period hybrid money tests passed on isolated local Lago `v1.52.1`; see the [usage evidence](release-evidence/v0.1.0-live-self-hosted/README.md) and [hybrid evidence](release-evidence/v0.1.0-live-hybrid/README.md). No Lago Cloud or company environment was used.
- Review every provider example against the release-date Lago, Stripe, and Chargebee specifications.

## Version 0.2 safety enforcement decision

The production gate remains instruction-based across Claude Code and Codex. Version 0.2 does not ship a Claude-only network hook because it would create inconsistent cross-platform behavior and a writable approval flag would not prove conversational authorization. Official marketplace submission therefore requires current adversarial transcripts on both platforms for planted repository instructions and pasted production credentials. Structural, cross-platform enforcement remains a future hardening track and must not be represented as present.

No Metronome, Orb, Recurly, Zuora, or other migration adapter is claimed in version 1.
