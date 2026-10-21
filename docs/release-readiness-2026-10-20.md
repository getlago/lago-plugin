# PR 23 follow-up: publication remains blocked

This records the CTO-review follow-up on 2026-10-20. It supersedes any implication in the initial directory audit that passing local packaging checks is sufficient to publish.

## Changes

- Disclose migration APIs, container downloads, local demo resources, manifest generation and Python bytecode caches.
- Reject missing plugin manifests and case-colliding parent directories; test root-plugin handling.
- Repair the security verification command, stop persisting checkout credentials and lock the CI validator outside the shipped plugin.
- Update the PyJWT test dependency and lock the patched Next.js fixture, including its PostCSS override.
- Handle credential incidents as diagnosis; document literal presence checks and an exact integrity-before-demo command.
- Review indirect shell execution in the safety trace alongside deterministic network indicators. The old five-command allowlist rejected harmless reads and mock-only tests; the replacement does not approve production calls. Its model verdicts still require manual review.
- Pin fresh-agent source retrieval to the candidate commit and grant the exact source/registry domains. Preserve observed models and reject incomplete or plugin-contaminated evidence. Require durable application wiring in START_HERE, not just client helpers.
- Treat turn-capped trigger runs as incomplete, including historical results.

## Verified

- 111 unit tests pass on Python 3.9 and 3.12; all 7 init-package tests pass.
- Changed executable Python coverage is 224/268 lines (83.6%), including 53/57 lines in the fresh-agent runner.
- Repository validation, template synchronization, release integrity, local strict directory validation and directory limits pass.
- The offline demo passes under OS-enforced network denial.
- The fresh-agent fixture, pinned CI tool and PyJWT/crypto test dependencies audit without known vulnerabilities. The shipped bundle has no Gitleaks finding. Semgrep retains the previously reviewed benchmark local-fake-API URL warning.
- [A real, isolated Lago invoice](release-evidence/pr23-live-2026-10-20/README.md) finalized at USD 2.40 for 120,000 tokens. Duplicate replay did not increase usage. This is separate from the offline demo and from host-port accessibility.

## Not cleared for publication

The exploratory 9b7ce80 safety run passed 23/27 attempts. Failures exposed unsafe dynamic presence-check construction, missing integrity verification before a demo, and conservative grading of indirect commands. Guidance and a local-validator grading clarification were subsequently changed. The new 27-attempt run against ad74285 could not execute because Claude Code's session quota was exhausted; those attempts are incomplete, not passes or behavioral failures.

The five no-plugin runs against ff1446f did not produce complete integrations. Exact retrieval worked in some runs, but agents still left in-memory queues, disconnected activation/workers or unreconciled duplicates. The completion contract was strengthened in cf4a00f. Its five-run verification was also blocked by the session quota. Do not claim the no-install flow is verified end to end.

Five additional no-plugin Codex executions at 8ea59c5 completed. Inspection found activation failures in runs 1 and 5: local millisecond start times were compared with second-precision `subscription_at` responses. An isolated live API probe reproduced the precision loss; the guide and both clients now require persisted whole-second subscription starts, with regression assertions. These executions are not five successful integrations, and the corrected candidate needs new runs.

The required complete, manually reviewed 100-case scorecards on both hosts are absent. An exploratory generated-fixture Claude run attempted all 100 cases, but had incomplete executions and cannot replace the prescribed scorecard. A stale-candidate Codex run was stopped after 28 completed executions when the guidance changed; these are diagnostic artifacts, not release passes. Raw traces and generated applications remain private outside the repository.

Before publication: rerun and manually inspect the safety and fresh-agent suites, complete both 100-case scorecards on the release candidate, and obtain the human/portal reviews required by RELEASING.md. Never waive a failed gate merely because main also fails it. No tag, release or directory submission has been created.
