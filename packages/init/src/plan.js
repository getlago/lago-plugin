import { existsSync, mkdirSync, readFileSync, writeFileSync, appendFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const templates = join(dirname(fileURLToPath(import.meta.url)), "../templates");
const ENV_LINES = ["LAGO_API_URL=", "LAGO_API_KEY=", "LAGO_WEBHOOK_HMAC_KEY="];

// Files to add for a detected stack. Paths follow the repository's layout.
export function planFiles(stack) {
  if (stack.language === "node") {
    // The template is TypeScript. JavaScript-only projects follow START_HERE.md instead.
    if (!stack.typescript) return [];
    const base = stack.srcDir ? "src/" : "";
    const files = [{ path: `${base}lib/lago-billing.ts`, template: "lago-billing.ts" }];
    if (stack.framework === "nextjs" && stack.appRouter) {
      files.push({ path: `${base}lib/lago-webhook-route.ts`, template: "webhook-route.ts" });
    }
    return files;
  }
  if (stack.language === "python") return [{ path: "lago_billing.py", template: "lago_billing.py" }];
  return [];
}

export function apply(dir, stack, { write }) {
  const actions = [];
  for (const file of planFiles(stack)) {
    const target = join(dir, file.path);
    if (existsSync(target)) {
      actions.push({ path: file.path, action: "skip (exists)" });
      continue;
    }
    actions.push({ path: file.path, action: write ? "created" : "would create" });
    if (write) {
      mkdirSync(dirname(target), { recursive: true });
      writeFileSync(target, readFileSync(join(templates, file.template), "utf8"));
    }
  }
  if (stack.language !== "unknown") {
    const envExample = join(dir, ".env.example");
    const existing = existsSync(envExample) ? readFileSync(envExample, "utf8") : "";
    const missing = ENV_LINES.filter((line) => !existing.split("\n").some((l) => l.startsWith(line)));
    if (missing.length) {
      actions.push({ path: ".env.example", action: write ? `added ${missing.join(" ")}` : `would add ${missing.join(" ")}` });
      if (write) appendFileSync(envExample, `${existing && !existing.endsWith("\n") ? "\n" : ""}${missing.join("\n")}\n`);
    }
  }
  return actions;
}
