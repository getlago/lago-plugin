# Fresh-agent integration check

Run against a clean, pushed candidate, with no plugin loaded:

```bash
python3 evals/fresh-agent/run.py --out "$TMPDIR/lago-fresh-candidate" --model claude-sonnet-5-5 --runs 5
```

The runner pins the START_HERE URL to the candidate commit and grants only the source, package registry and Lago documentation domains. An unqualified `WebFetch` grant does **not** enable shell downloads in the eval sandbox ([official isolation rules](https://code.claude.com/docs/en/plugin-evals)). A blocked source download is incomplete integration evidence, never proof that the template works.

Judge actual billing behavior across Write, Edit and shell copies. Manually inspect the saved generated files and trace before accepting a release; LLM graders can be wrong. The fixture's memory-only database is deliberately insufficient for production: a complete integration must add durable usage and webhook work. The fixture uses locked Next.js dependencies; its PostCSS override fixes the upstream transitive version retained by Next 15. Do not deploy the fixture.

`summary.json` records the commit, CLI version, observed models, completeness and each run's failures. Raw traces remain private outside the repository. No plugin, key or pre-copied Lago module is supplied to the agent.
