import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const read = (dir, file) => (existsSync(join(dir, file)) ? readFileSync(join(dir, file), "utf8") : null);

// Classify the application from its manifests. Evidence only; never execute project code.
export function detectStack(dir) {
  const pkg = read(dir, "package.json");
  if (pkg) {
    let manifest;
    try {
      manifest = JSON.parse(pkg);
    } catch {
      return { language: "node", framework: "unknown", evidence: ["package.json (unparseable)"] };
    }
    const deps = { ...manifest.dependencies, ...manifest.devDependencies };
    const framework = deps.next ? "nextjs" : deps.express ? "express" : deps.fastify ? "fastify" : "node";
    const appRouter = framework === "nextjs" && (existsSync(join(dir, "app")) || existsSync(join(dir, "src/app")));
    return {
      language: "node",
      framework,
      typescript: Boolean(deps.typescript) || existsSync(join(dir, "tsconfig.json")),
      srcDir: existsSync(join(dir, "src")),
      appRouter,
      evidence: ["package.json", ...(appRouter ? ["app router"] : [])],
    };
  }
  const python = [read(dir, "pyproject.toml"), read(dir, "requirements.txt")].filter(Boolean).join("\n").toLowerCase();
  if (python) {
    const framework = /\bfastapi\b/.test(python) ? "fastapi" : /\bdjango\b/.test(python) ? "django" : /\bflask\b/.test(python) ? "flask" : "python";
    return { language: "python", framework, evidence: [existsSync(join(dir, "pyproject.toml")) ? "pyproject.toml" : "requirements.txt"] };
  }
  return { language: "unknown", framework: "unknown", evidence: [] };
}
