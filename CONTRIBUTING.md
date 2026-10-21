# Contributing

Use public primary sources and synthetic data. Keep the main skill compact; add conditional detail to the narrowest reference. Do not add MCP, telemetry, runtime credentials, production actions, internal Lago material, or a new skill without an accepted architecture change. An architecture change is accepted when its entry in [docs/architecture.md](docs/architecture.md) is approved in the pull request that implements it. That pull request also updates every skill reference, validator signal, test, and eval case that enforced the previous rule.

For behavior changes, add or update an eval case and test observable outcomes. Run:

```bash
python3 scripts/validate_repo.py .
python3 -m unittest discover -s tests -v
python3 tools/release/release_integrity.py check plugins/lago --manifest tools/release/RELEASE-MANIFEST.json
claude plugin validate .
claude plugin validate plugins/lago --profile directory --strict
python3 scripts/check_directory_limits.py plugins/lago
```

After any change in `plugins/lago/`, regenerate `tools/release/RELEASE-MANIFEST.json` before the final validation commit. Never “fix” an integrity failure by updating only the hash without reviewing the changed file.

Document version-sensitive claims with a focused official link. Report offline and live validation separately. Use conventional commits and include changed behavior, evidence, risks, and compatibility in the pull request.
