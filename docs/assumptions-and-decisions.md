# Assumptions and unresolved decisions

## Assumptions

- Repository and future GitHub location: `getlago/lago-agent-plugin`.
- Plugin slug: `lago-billing`; marketplace slug: `lago-plugins`; initial version: `0.1.0`; license: MIT.
- Python 3.10+ is acceptable for optional offline validators; skill loading has no runtime dependency.
- Lago's official docs and OpenAPI remain the authority for version-sensitive behavior.

## Decisions required before publication

- Confirm Lago legal/brand approval for the plugin name, MIT license, and publisher metadata.
- Confirm which Lago-owned marketplace/catalog, if any, will list the plugin.
- Decide the supported minimum Claude Code and Codex versions after clean-machine testing.
- Run and archive at least one authorized live Lago sandbox money test; local fixtures prove the calculation harness, not Lago runtime behavior.
- Review every provider example against the release-date Lago, Stripe, and Chargebee specifications.

No Metronome, Orb, Recurly, Zuora, or other migration adapter is claimed in version 1.
