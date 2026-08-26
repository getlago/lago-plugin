# Eval suite

`cases.json` contains 49 synthetic scenarios. Run each in a fresh task against a minimal synthetic repository and score the actual output with `scorecard.md`.

Deterministic preflight:

```bash
python3 skills/implementation/scripts/validate_repo.py .
python3 -m unittest discover -s tests -v
```

Behavioral evals must inspect actual edits, test evidence, source links, authorization pauses, and final handoff—not keyword matching alone. Use no real companies, credentials, billing records, or production systems. For live demo money tests, use a separately approved isolated self-hosted Lago instance and sanitized evidence; never use Lago Cloud.
