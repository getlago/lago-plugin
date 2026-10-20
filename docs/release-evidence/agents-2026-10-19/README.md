# Agent install verification, 2026-10-19

`evals/agent-installs/verify_installs.py` installs this repository with the real CLIs of other agents. Each CLI runs in a temporary HOME, so no user configuration or credentials are read or changed. The original checks below tested install and discovery only. They did not test the installed bundle integrity gate or the offline demo. The corrected runner additionally requires both for full-bundle installs and verifies Copilot’s configured source path.

Run at clean commit `9d3593c37233fa81c480dee2f33ad09cd61f24f4` with Node v24.2.0. The raw output is in [verify-installs-9d3593c.json](verify-installs-9d3593c.json); temporary paths are redacted.

| Agent | CLI | Commands | Result |
| --- | --- | --- | --- |
| Gemini CLI | `@google/gemini-cli@0.64.0` | `extensions validate`, `extensions install <checkout> --consent`, `skills list` | Pass. `implementation [Enabled]`, one identical `SKILL.md`, full bundle including `RELEASE-MANIFEST.json` |
| GitHub Copilot CLI | `@github/copilot@1.0.100` | `plugin marketplace add <checkout>`, `plugin install lago@lago-plugins`, `plugin list` | Pass. "Installed 1 skill", `lago@lago-plugins` enabled. A local marketplace loads live from the checkout, so nothing is copied |
| skills.sh | `skills@1.7.4` | `add <checkout> --skill implementation -a codex -a cursor -a github-copilot -a gemini-cli --copy -y` | Pass. One identical `SKILL.md` in `.agents/skills/implementation/`. The skill alone ships without `RELEASE-MANIFEST.json`, as expected |

A separate manual check ran the README command against GitHub at the same commit, again in a temporary HOME:

```bash
gemini extensions install https://github.com/getlago/lago-plugin --ref 9d3593c37233fa81c480dee2f33ad09cd61f24f4 --consent
```

Gemini CLI 0.64.0 installed it, and `skills list` showed `implementation [Enabled]`. The installed `SKILL.md` hash is `03ecfca42b3c10fcf315e178c07bd15f825e13f1dd7c534202b5540c308335b3`, identical to the checkout's.

## CTO review correction

The original Gemini check was insufficient: `.gemini-extension-install.json`, written by Gemini CLI after installation, caused release integrity to fail on an unexpected file. Merely finding `RELEASE-MANIFEST.json` did not prove the demo could run. The verifier now permits that exact root bookkeeping file only for a Gemini bundle; modified payloads, symlinks and other extra files still fail. No production approval or billing guidance changed.

The corrected runner verifies the whole installed Gemini bundle, runs its offline demo only after integrity passes, and verifies Copilot’s enabled setting and marketplace source against the checkout before accepting its live-loaded bundle. Failure evidence is sanitized, and `--allow-dirty` cannot label a report complete.

### Corrected clean-commit run

[verify-installs-c4a210e.json](verify-installs-c4a210e.json) records a fresh run at clean commit `c4a210e02ddaf0c4e7bdc6dcf737e35c8791b346`, Node v25.5.0, with no source change during the checks. All three checks passed:

- Gemini CLI 0.64.0: validation, install, enabled skill discovery, identical skill, full bundle integrity (230 files, only the CLI install record exempted), and the installed offline demo.
- Copilot CLI 1.0.100: local marketplace install, enabled state and exact source binding from settings, identical skill, full bundle integrity and offline demo.
- skills.sh 1.7.4: identical skill-only copy; no claim that the full bundle or root examples were installed.

Command: `python3 evals/agent-installs/verify_installs.py`. No credentials or model session were used. The report has `complete: true`, `source_dirty: false` and `source_changed: false`. The subsequent evidence commit changes documentation and the release manifest, not the tested runtime or packaging code.

## What this does not show

- Whether any of these agents selects the skill from a user prompt. That needs an authenticated model session per agent; triggering was measured only for Claude Code and Codex (see [evals/triggers](../../../evals/triggers/README.md)).
- Copilot CLI installed from GitHub: `copilot plugin marketplace add getlago/lago-plugin` reads the default branch, so it can be checked only after merge.
- Cursor, Goose, Devin, Amp, OpenCode, Cline, and Kiro were not tested. No CLI was available, or it needed an account. The Cursor manifests follow https://cursor.com/docs/reference/plugins.md and are unverified in Cursor itself.
