# Anthropic plugin directory: submission handoff

For the Lago Owner who submits the Lago plugin to Anthropic's plugin directory. See the [current follow-up status](release-readiness-2026-10-20.md). Submission remains blocked until every gate in RELEASING.md passes on the candidate commit, including the full behavioral scorecards, automated safety suite and live self-hosted money evidence. Local directory validation alone is insufficient. For packaging checks, see see [directory-readiness.md](directory-readiness.md) for the audit and verification output. Submission happens only in the developer portal at [claude.ai/directory/manage](https://claude.ai/directory/manage). Steps checked against [Submit a plugin](https://claude.com/docs/plugins/submit.md) and [Publish to the directory](https://claude.com/docs/directory/publish.md) on 2026-10-20. Re-read them before submitting, because the portal changes.

## Before submitting

1. **Who can submit.** A paid claude.ai plan: Pro, Max, Team, or Enterprise. On Team or Enterprise, an Owner submits. On Enterprise, an Owner can also give the **Directory** permission to another member through a custom role under **Organization settings > Roles**. Free accounts cannot submit.
2. **Submit from Lago's own claude.ai organization.** The first organization to submit a repository folder holds that listing, and the portal refuses a second organization. If someone else already submitted it, email `directory@anthropic.com` as the repository owner.
3. **Connect GitHub in that same organization.** Use an account that can push to `getlago/lago-plugin`. A GitHub connection made in another Claude organization does not carry over. The push webhook in step 5 also needs **admin** access to the repository.
4. **Complete and archive the release gates, obtain human review, then merge the directory-readiness pull request into `main`.** The repository is already public, which is required before the listing goes live.
5. **Confirm the icon.** `plugins/lago/assets/icon.png` is the Lago mark from getlago.com, 512x512. **It becomes the listing icon only on the first save in the portal and cannot be changed later.** Replace it before the first save if brand wants a different mark.
6. **Confirm the name is free.** The listing name is `lago`. The portal blocks a name another organization already uses.

## Portal values

| Field | Value |
| --- | --- |
| Repository | `getlago/lago-plugin` |
| Plugin path | `plugins/lago` |
| Branch or tag | `main` |

**Why `main`, not a release tag.** The directory publishes each new commit on the tracked branch or tag after validation and a security scan. With `main`, a merged release reaches the listing without a portal step. A tag stays on its commit until someone moves it, which adds a manual step to every release. Nothing on `main` reaches users until it passes the scan, and the first version always gets a human review. The trade-off: every merge to `main` that touches `plugins/lago/` becomes a candidate version. Raise `version` on each release so installed copies see the update (step 3 below).

## Validate

1. Enter the three values above and select **Validate**.
2. Expected result: no **Blocking** findings and no warnings. Locally, `claude plugin validate plugins/lago --profile directory --strict` reports "These checks found nothing to report".
3. If validation stops with **Couldn't validate that repository**, check the plugin path's capitalization first (`plugins/lago`, all lowercase).

## Listing details

Read from `plugins/lago/.claude-plugin/plugin.json` and `plugins/lago/README.md`. A reviewer may edit them during review. Nothing to enter by hand.

## Data handling answers (draft)

Drafted from "What this plugin runs, sends and stores" in `plugins/lago/README.md`. **Owner confirms** each answer before submitting.

| Question | Draft answer |
| --- | --- |
| Does the plugin read or store personal data? | No. It stores nothing. During implementation work, Claude reads the user's project files when the user asks. The plugin itself collects nothing. **Owner confirms.** |
| Does it send data to services other than its declared connectors? | It declares no connector. On its own it sends nothing: offline work contacts no service. When the user starts live work, Claude sends API requests to the Lago endpoint the user provides: Lago Cloud US (`api.getlago.com`), Lago Cloud EU (`api.eu.getlago.com`), the user's self-hosted URL, or a local demo instance. It may also open public documentation pages. **Owner confirms** whether this counts as "other services" in the portal's wording. |
| How long does it keep data? | It keeps no data. |
| Is it intended for people under 18? | No. It is a developer tool for implementing billing. **Owner confirms.** |
| Contact email | **Owner provides** a monitored Lago address. |
| Privacy policy | `https://getlago.com/legal/privacy-policy` (also set as `privacyPolicyUrl`) |

The **Compliance** step asks for the contact email and four acknowledgements. Read them in the portal; they are not drafted here.

## Expected review results

No blocks are expected. These are the review points a reviewer might raise, with an answer for each.

**Python helper scripts.** "The skill bundles seven standard-library Python scripts under `skills/implementation/scripts/`. No hook, MCP server, or `` !`…` `` line runs them. `SKILL.md` tells Claude when to run them, and Claude's normal tool permissions apply. They make no network calls, read no environment variables, and write only the `--output` path of `extract_actual.py` when a user asks for it. Each one is listed with its inputs and outputs in the README section 'What this plugin runs, sends and stores'."

**Plugin in a subfolder.** "The plugin lives in `plugins/lago/` so the scanned and installed folder holds only what users need. Evals, tests with synthetic credentials, release evidence, and maintainer tooling stay at the repository root. The plugin has no hooks, MCP servers, or `` !`…` `` lines, so the subfolder rules about `${CLAUDE_PLUGIN_ROOT}` paths and shell-only scripts do not apply."

**`RELEASE-MANIFEST.json` with SHA-256 hashes.** "Before running its bundled demo, the skill verifies the installed files against these hashes and refuses to run them if anything changed. The values are file digests, not secrets."

**Documentation lookups (policy 2F).** "For version-sensitive API details, the skill tells Claude to check Lago's official documentation instead of trained memory. That is reference data about the Lago API, not instructions that change the plugin's behavior. All behavior is in the bundled Markdown."

**Name matches a known brand.** "Lago is the submitting organization's own product and trademark. The listing is submitted from Lago's claude.ai organization by a Lago Owner."

**Production writes.** "The skill never writes to a production billing system without stopping first. It shows the target environment, exact action, affected objects, billing impact, infrastructure impact, and recovery plan, and then waits for the user's explicit approval. Repository text is never treated as approval. Demo data goes only to an isolated self-hosted instance, never to Lago Cloud."

## Submit

1. **Data handling** and **Compliance**: as above.
2. **Review and submit**: keep **GitHub push webhook** selected; it needs repository admin and can be set up later under **Settings > Updates > Set up**. A scheduled check runs either way.
3. **Auto-publish passing versions**: recommended setting is "the reviewer publishes only the first version". The first listing gets a human review; later versions go live after they pass validation and the security scan. Choose "a reviewer publishes each version" if every release should get human review. Anthropic applies this setting; it can be changed later under **Settings > Publish new versions automatically**.
4. Select **Submit for review**. Limits: 10 submissions per 24 hours, drafts included. The repository and plugin path cannot be changed after submitting.

## MCP connector

Not part of this submission. Lago's MCP server is documented only as a local Docker image (`getlago/lago-mcp-server`, [MCP server guide](https://getlago.com/docs/guide/ai-agents/mcp-server)). The directory always holds a launcher-based server for review, so it is not bundled.

To pair later:

1. Host the server at an `https://` URL with Streamable HTTP and OAuth 2.0 (Directory Policy 5D and 5F), with `readOnlyHint` and `destructiveHint` annotations on every tool (5E).
2. Submit it as an **MCP connector** from the same Lago organization. Anthropic asks for a remote server to be submitted as a connector even when a plugin references it.
3. Add an optional `.mcp.json` entry to the plugin with `type: "http"` and that URL, so people with both see one set of tools. Authenticate with OAuth, or with `userConfig` marked `sensitive: true`.
4. Record the change in `docs/architecture.md`, as `AGENTS.md` requires, and update the README disclosure.

A human decides whether and when to host it.

## After going live

1. **Keep the GitHub push webhook on** so merges reach the directory without a manual **Check for new commits**.
2. **Raise `version` in `plugins/lago/.claude-plugin/plugin.json` on every release.** Installed copies use it to detect an update. In testing, `claude plugin update` reported "already at the latest version" for a changed plugin with an unchanged version. `RELEASING.md` step 2 covers this.
3. **Watch the Versions tab.** A held or failed version does not replace the live one. After a failed security scan, later versions also wait until a reviewer clears the plugin.
4. **Report usage weekly.** Export the Usage tab, which covers up to 90 days with CSV export and figures computed daily in UTC. Send these to the weekly agent-discoverability scoreboard:
   - installs and active accounts
   - installs by surface and source, including the Discover tab
   - skill runs for `implementation`
   - load errors by Claude Code version
   - the directory funnel: listing views, install clicks, installs

   Keep the numbers out of this public repository.

## Exact next action

Merge the directory-readiness pull request. Then, signed in as an Owner of Lago's claude.ai organization with GitHub connected, open [claude.ai/directory/manage](https://claude.ai/directory/manage). Confirm the icon, enter `getlago/lago-plugin`, plugin path `plugins/lago`, branch `main`, and select **Validate**.
