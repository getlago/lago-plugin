# Competitive benchmark

Inspected 2026-08-26 from the public repositories [Zuora](https://github.com/zuora/zuora-coding-agent), [Metronome](https://github.com/Metronome-Industries/ai), [Stripe](https://github.com/stripe/ai), and [Polar](https://github.com/polarsource/skills). This compares repository capabilities, not vendor product completeness.

| Capability | Lago proposal | Zuora | Metronome | Stripe | Polar |
| --- | --- | --- | --- | --- | --- |
| Repository discovery | Required first pass | Per-skill/context | Limited | Framework/project skills | Setup-oriented |
| Cloud support | Yes, US/EU routing | Vendor tenant | Yes | Yes | Yes |
| Self-hosted support | Docker evaluation + Helm production path | No | No | No | No |
| Implementation | End-to-end mode | Strong design/build split | Strong catalog/workflows | Strong API guidance | Simple integration flow |
| Usage-event design | Canonical contract + edge cases | Meter-specific | Excellent | Strong | Basic |
| Pricing-model design | Subscription/usage/credits/commitments/hybrid | Broad | Excellent | Broad Billing | Product/price focused |
| Migration | Stripe, Chargebee, custom | Several Zuora migrations | Deep Stripe migration | SDK/API migrations | Broad but lightweight |
| Testing | Unit/integration/synthetic/evals | UAT and linters | Dogfood scenarios | Executable benchmarks | Sandbox checklist |
| Invoice validation | Deterministic money test | Validation skills | Definitive invoice scorecard | Benchmark-specific | Basic sandbox checks |
| Reconciliation | Read-only cross-system mechanism | Partial | Parallel parity checks | Scenario-specific | Post-migration checks |
| Deployment | Cloud config + self-hosted | Minimal | Minimal | Minimal | Minimal |
| Troubleshooting | Evidence-led full path | Product skills | Diagnostic references | Domain guidance | Common issues |
| Safety | Exact-action production gates | Sandbox warning/credentials | Strong cutover rules | Excellent secret/tax/webhook rules | Sandbox-first |
| MCP dependency | None; optional later | Required for major flows | None | Optional | None |
| Claude support | Native plugin | Native plugin | Portable skills | Portable skills | Portable skills |
| Codex support | Native plugin | Native plugin | Portable skills | Portable skills | Portable skills |
| Eval quality | 41 cases + deterministic suite | UAT/linters | Manual scorecards | Executable benchmarks | Checklists |
| Installation complexity | No credentials/dependencies | MCP + Node + credentials | Copy/install skills | Skills/MCP options | Low |

Adopted patterns: Zuora's dual packaging and deterministic tools; Metronome's routing tables, mapping ledgers, parallel-run protections, and money tests; Stripe's source/version/secret/webhook discipline; Polar's straightforward onboarding. Deliberately omitted: mandatory MCP, runtime credentials, vendor-specific instructions, and many overlapping skills.
