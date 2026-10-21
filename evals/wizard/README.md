# Pricing-first wizard evaluation

Run each case from `cases.json` in a fresh agent task with the plugin installed from this branch. Use a synthetic application repository and no real credentials, customer data, or production Lago target. Score the observed sequence and output against every signal; keyword presence alone is not a pass. For URL and file cases, replace placeholders with a local fixture or a public synthetic page and record which source was actually read.

The proof-boundary case should be checked against the [saved growth-agent adapter evidence](https://github.com/anhtho-lago/growth-agent-billing-lab/tree/main/evals/runs/2026-10-20-agent-adapter). The $1,250 usage charge and retry recovery passed in an isolated self-hosted run. The expected $1,750 invoice total and payment collection were not verified.

These cases define acceptance criteria; adding them is not evidence that a fresh agent run passed.
