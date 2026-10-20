# Agent install verification, 2026-10-19

`evals/agent-installs/verify_installs.py` installs this repository with the real CLIs of other agents. Each CLI runs in a temporary HOME, so no user configuration or credentials are read or changed. A check passes only when the CLI reports success. Gemini CLI and skills.sh must also install a `SKILL.md` that is byte-identical to the checkout's.

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

## What this does not show

- Whether any of these agents selects the skill from a user prompt. That needs an authenticated model session per agent; triggering was measured only for Claude Code and Codex (see [evals/triggers](../../../evals/triggers/README.md)).
- Copilot CLI installed from GitHub: `copilot plugin marketplace add getlago/lago-plugin` reads the default branch, so it can be checked only after merge.
- Cursor, Goose, Devin, Amp, OpenCode, Cline, and Kiro were not tested. No CLI was available, or it needed an account. The Cursor manifests follow https://cursor.com/docs/reference/plugins.md and are unverified in Cursor itself.
