#!/usr/bin/env node
import { resolve } from "node:path";
import { detectStack } from "../src/detect.js";
import { apply } from "../src/plan.js";

const START_HERE = "https://github.com/getlago/lago-plugin/blob/main/START_HERE.md";
const args = process.argv.slice(2);
if (args.includes("--help") || args.includes("-h")) {
  console.log(`Usage: lago-init [dir] [--write] [--json]

Detects a Node.js or Python application and scaffolds Lago usage-based billing:
a billing module, a webhook route for the Next.js App Router, and .env.example keys.
Dry run by default. --write creates files; existing files are never overwritten.
No network calls, no credentials, no package installs.`);
  process.exit(0);
}
const dir = resolve(args.find((a) => !a.startsWith("-")) ?? ".");
const write = args.includes("--write");
const stack = detectStack(dir);
const actions = apply(dir, stack, { write });

if (args.includes("--json")) {
  console.log(JSON.stringify({ dir, stack, write, actions }, null, 2));
  process.exit(stack.language === "unknown" ? 2 : 0);
}

console.log(`Lago init${write ? "" : " (dry run)"}: ${dir}`);
if (stack.language === "unknown") {
  console.log("No package.json, pyproject.toml, or requirements.txt found. Open the application directory, or follow", START_HERE);
  process.exit(2);
}
console.log(`Detected: ${stack.language} / ${stack.framework} (${stack.evidence.join(", ")})`);
for (const { path, action } of actions) console.log(`  ${action.padEnd(14)} ${path}`);
console.log(`
Next:
  1. See the money first, offline: git clone --depth 1 https://github.com/getlago/lago-plugin.git && python3 lago-plugin/plugins/lago/skills/implementation/scripts/run_demo.py
  2. Set LAGO_API_URL (ask for the region: US https://api.getlago.com, EU https://api.eu.getlago.com, or self-hosted) and LAGO_API_KEY in the secret manager.
  3. Create the metric and plan once, then wire customers, subscriptions, usage, and webhooks: ${START_HERE}
  4. Optional, guided help in your agent:
     In an interactive Claude Code session, run each command separately:
       /plugin marketplace add getlago/lago-plugin
       /plugin install lago@lago-plugins
     After installation, ask: /lago:implementation show me what Lago can do
     For Codex, run each command separately in your terminal:
       codex plugin marketplace add getlago/lago-plugin
       codex plugin add lago@lago-plugins
     Start a new Codex task, then ask: $lago:implementation show me what Lago can do
${write ? "" : "\nRe-run with --write to create the files."}`);
