# Releasing

1. Confirm public-source and brand/legal review; run the private denylist audit.
2. Update both manifests, `CHANGELOG.md`, and any documented minimum platform versions to the same semantic version.
3. Run repository tests, skill validation, Claude validation, Codex plugin validation, broken-link/secret scans, all 41 behavioral evals, and one authorized live Lago sandbox money test.
4. Test install, explicit invocation, automatic routing, update, and uninstall from clean Claude Code and Codex environments with MCP unavailable.
5. Tag `vX.Y.Z` from a clean commit and publish release notes. Do not publish or submit to a marketplace without explicit maintainer approval.

Patch releases fix guidance or validators; minor releases add backward-compatible modes/adapters; major releases change contracts, installation, or safety behavior.
