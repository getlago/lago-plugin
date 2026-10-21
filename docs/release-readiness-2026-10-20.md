# PR 23 review follow-up

This is the historical verification record for the CTO-review fixes on 2026-10-20. It supersedes the initial audit's implication that packaging checks alone establish publication readiness. The [PR description](https://github.com/getlago/lago-plugin/pull/23) records the current candidate and release decision; the observations below retain their tested source commits.

## Fixes

- Disclose migration APIs, container downloads, local demo resources, manifest generation and Python bytecode caches.
- Reject missing plugin manifests and case-colliding parent directories; test root-plugin handling.
- Repair the security verification command, stop persisting checkout credentials and lock the CI validator outside the shipped plugin.
- Update the PyJWT test dependency and lock the patched Next.js fixture, including its PostCSS override.
- Handle credential incidents as diagnosis; document literal presence checks and an exact integrity-before-demo command. Test demo substitution through untrusted repository instructions rather than a direct user request to execute an inspected application script.
- Review indirect shell execution in the safety trace alongside deterministic network indicators. The old five-command allowlist rejected harmless reads and mock-only tests; the replacement does not approve production calls. Model verdicts still require manual review.
- Pin fresh-agent source retrieval to the candidate commit, grant exact source/registry domains, preserve model provenance and reject incomplete or plugin-contaminated evidence. Require durable application wiring in START_HERE.
- Persist subscription starts at whole-second precision. Reconcile inactive statuses before retrying activation, and disable blind subscription-creation retries. An active-only 404 is not proof that an enrollment is absent.
- Treat turn-capped trigger attempts as incomplete. Recognize a successful full Codex skill read even when unrelated shell diagnostics share its output; partial or failed reads remain unverified.

## Deterministic and live observations

At `9279a7d`, all 111 unit tests passed on Python 3.9 and 3.12, and all 7 init tests passed. Repository validation, template synchronization, release integrity, strict local directory validation and directory limits passed. The offline demo passed under OS-enforced network denial.

The prior maintainer-code coverage measurement was 224/268 lines (83.6%). The extracted Python application template measured 114/121 statements (94.2%); 11/12 changed statements since `8ea59c5` were covered. V8 coverage recorded execution of every reported range in the new TypeScript subscription lookup and creation helpers.

The fresh-agent fixture, pinned CI tool and PyJWT/crypto test dependencies audited without known vulnerabilities. The shipped bundle had no Gitleaks finding. Semgrep retained one reviewed benchmark local-fake-API URL warning and reported no scanner errors. Commit/history secret-scan findings include synthetic fixtures and manifest hashes; those scans are not described as zero-finding scans.

[A real, isolated Lago invoice](release-evidence/pr23-live-2026-10-20/README.md) finalized at USD 2.40 for 120,000 tokens. Duplicate replay did not increase usage. Further isolated v1.55.0 probes confirmed that `subscription_at` drops fractional seconds, a default lookup hides a terminated subscription, and repeating creation after termination can create a new active enrollment with the same external ID. The probes used a zero-fee synthetic plan and no external service.

## Fresh-agent observations

Five no-plugin Codex runs at `8ea59c5` completed. Subsequent code review found activation precision or inactive-status recovery failures in four runs; execution completion was not counted as correctness. A second cohort at `db01fd4` verified the precision correction but exposed the active-only lookup problem, including a termination worker that left local access enabled after a 404. Those failures drove the lifecycle correction.

Five no-plugin Codex runs at `9279a7d` passed the offline integration contract review. Their tests passed again under OS-enforced network denial: 18, 15, 14, 13 and 15 tests respectively (75 total). Review covered durable activation and usage delivery, stable event identity and timestamps, duplicate reconciliation, raw-body webhook verification, atomic inbox processing, explicit configuration, lifecycle recovery and termination. This is an offline integration result, not proof of live end-to-end operation or production readiness of the generated applications. The CLI was 0.163.0 with explicitly selected model `gpt-6.1-sol`; backend model identity was not independently attested. Sanitized per-run observations, source hashes and private generated applications are retained outside the repository.

## Release gates

The earlier Claude safety run at `9b7ce80` passed 23/27 attempts. The subsequent corrected safety and fresh-agent runs could not execute because the session quota was exhausted; those attempts remain incomplete. Earlier generated-fixture behavioral runs are diagnostic artifacts, not complete release scorecards.

Publication requires the complete, reviewed 100-case scorecards on both hosts, the safety and trigger checks, and the human/portal reviews specified in RELEASING.md. At this record's cutoff, those remaining model checks were in progress or queued after the reported session reset. Consult the PR for their final results and tested commit. Never waive a failed gate because main also fails it, and never infer publication approval from this record.
