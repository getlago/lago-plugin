# Historical START_HERE fresh-agent evidence

These are recovered artifacts from the original 2026-10-19 run, before the PR #14 correctness fixes. They are not a validation of the corrected code, and the original graders did not cover redirect leakage, lost enqueueing, wallet restrictions, or proration.

## Provenance and limits

- Claude Code 2.1.304; started 2026-10-19T23:51:51.903Z; two runs per arm, with/without plugin.
- The original prompt fetched a mutable `feat/start-here` URL. The harness did not record a source commit or content digest. Exact fetched-source provenance therefore cannot be certified retrospectively.
- `START_HERE.snapshot.md` preserves the pre-fix repository page from commit `da54f911d57f0d0c1a7ea92c1957975332631244`, SHA-256 `2f66ca6bb99eb4c6e0a2320509a2de0c8b97fa2115d31709e26b6c80da1ca808`. This is a reference snapshot, not a claim that the harness verified this digest.
- The eval prompt is now pinned to an immutable source revision. Future runs must archive that revision, the exact command and the resulting artifacts; never replace it with a moving branch or silently carry these results forward.

## Results as recorded

| Arm | Run | All graders passed | Turns |
| --- | --- | --- | --- |
| With plugin | 1 | Yes | 35 |
| With plugin | 2 | No | 33 |
| Without plugin | 1 | Yes | 21 |
| Without plugin | 2 | Yes | 20 |

The second with-plugin run failed `correct-integration` with `judge votes: FAIL FAIL FAIL`. The artifact contains no itemized judge rationale. This remains a failure; no manual override is applied. The suite's recorded threshold was **0**, so successful process completion is not evidence that all graders passed.

## Artifacts

- [Harness results and grader definitions](aggregate-result.json), retaining scores, costs, errors, votes and explanations.
- [With-plugin run 1](with-1.json) and [run 2](with-2.json).
- [Without-plugin run 1](without-1.json) and [run 2](without-2.json).

Each transcript preserves conversation content, tool inputs (including generated file contents and edits), tool results, and the final result. Runtime initialization/account/session metadata and redundant embedded grader traces were omitted. Local paths were replaced with `[LOCAL_PATH]`; generated application paths use `[APP]/` so edits remain attributable. These are sanitized conversation exports, not executable fixtures or new benchmark runs. Review the Write/Edit calls alongside their tool results; the transcripts also retain the failed installs and type-check limitations.

## Re-run the corrected case

The corrected source is pinned to `bad552417a033500cea4bce3c72a3d1b224897dd` in the eval prompt. From the reviewed PR checkout, run:

```bash
claude plugin eval . --eval-dir evals/fresh-agent --case nextjs-start-here --ablation with-without --runs 2 --scaffold --allow-tools Bash Write Edit WebFetch --no-publish --keep-temp --threshold 1 --output-dir ../lago-start-here-eval-results
```

This is the reproduction command for a future corrected run, not a claim that it has been run. Use a trusted fixture, archive its outputs outside the release bundle while running, and sanitize the resulting transcripts before committing evidence. This case measures a URL-guided integration, not unprompted vendor selection. Update the source pin and regenerate the release manifest whenever the guide changes; retain each run's original source revision.
