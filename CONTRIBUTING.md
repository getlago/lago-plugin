# Contributing

Use public primary sources and synthetic data. Keep the main skill compact; add conditional detail to the narrowest reference. Do not add MCP, telemetry, runtime credentials, production actions, internal Lago material, or a new skill without an accepted architecture change.

For behavior changes, add or update an eval case and test observable outcomes. Run:

```bash
python3 skills/implementation/scripts/validate_repo.py .
python3 -m unittest discover -s tests -v
claude plugin validate .
```

Document version-sensitive claims with a focused official link. Report offline and live validation separately. Use conventional commits and include changed behavior, evidence, risks, and compatibility in the pull request.
