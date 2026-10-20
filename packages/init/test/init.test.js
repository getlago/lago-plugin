import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { detectStack } from "../src/detect.js";

const pkg = join(dirname(fileURLToPath(import.meta.url)), "..");
const cli = join(pkg, "bin/lago-init.js");

function fixture(files) {
  const dir = mkdtempSync(join(tmpdir(), "lago-init-"));
  for (const [path, body] of Object.entries(files)) {
    mkdirSync(dirname(join(dir, path)), { recursive: true });
    writeFileSync(join(dir, path), body);
  }
  return dir;
}

const run = (dir, ...flags) => JSON.parse(execFileSync("node", [cli, dir, "--json", ...flags], { encoding: "utf8" }));

test("detects a Next.js App Router project", () => {
  const dir = fixture({ "package.json": JSON.stringify({ dependencies: { next: "15.0.0" }, devDependencies: { typescript: "5.6.0" } }), "app/page.tsx": "" });
  assert.deepEqual(
    { ...detectStack(dir), evidence: undefined },
    { language: "node", framework: "nextjs", typescript: true, srcDir: false, appRouter: true, evidence: undefined },
  );
  rmSync(dir, { recursive: true });
});

test("detects Python frameworks from pyproject or requirements", () => {
  for (const [file, body, framework] of [["pyproject.toml", 'dependencies = ["fastapi>=0.110"]', "fastapi"], ["requirements.txt", "Django==5.1\n", "django"], ["requirements.txt", "flask\n", "flask"]]) {
    const dir = fixture({ [file]: body });
    assert.equal(detectStack(dir).framework, framework);
    rmSync(dir, { recursive: true });
  }
});

test("dry run writes nothing", () => {
  const dir = fixture({ "package.json": JSON.stringify({ dependencies: { next: "15.0.0" } }), "tsconfig.json": "{}", "src/app/page.tsx": "" });
  const result = run(dir);
  assert.deepEqual(result.actions.map((a) => [a.path, a.action.split(" ")[0]]), [
    ["src/lib/lago-billing.ts", "would"],
    ["src/lib/lago-webhook-route.ts", "would"],
    [".env.example", "would"],
  ]);
  assert.equal(existsSync(join(dir, "src/lib")), false);
  assert.equal(existsSync(join(dir, ".env.example")), false);
  rmSync(dir, { recursive: true });
});

test("--write creates files from START_HERE.md and never overwrites", () => {
  const dir = fixture({ "requirements.txt": "fastapi\n", "lago_billing.py": "# mine\n", ".env.example": "DATABASE_URL=x" });
  const result = run(dir, "--write");
  assert.deepEqual(result.actions[0], { path: "lago_billing.py", action: "skip (exists)" });
  assert.equal(readFileSync(join(dir, "lago_billing.py"), "utf8"), "# mine\n");
  assert.equal(readFileSync(join(dir, ".env.example"), "utf8"), "DATABASE_URL=x\nLAGO_API_URL=\nLAGO_API_KEY=\nLAGO_WEBHOOK_HMAC_KEY=\n");
  rmSync(join(dir, "lago_billing.py"));
  run(dir, "--write");
  assert.equal(readFileSync(join(dir, "lago_billing.py"), "utf8"), readFileSync(join(pkg, "templates/lago_billing.py"), "utf8"));
  assert.equal(run(dir, "--write").actions.length, 1, "second run adds nothing to .env.example");
  rmSync(dir, { recursive: true });
});

test("JavaScript-only Node projects get guidance, not TypeScript files", () => {
  const dir = fixture({ "package.json": JSON.stringify({ dependencies: { express: "4.0.0" } }) });
  assert.deepEqual(run(dir).actions.map((a) => a.path), [".env.example"]);
  rmSync(dir, { recursive: true });
});

test("unknown directory exits 2 without writing", () => {
  const dir = fixture({ "README.md": "docs" });
  const result = spawnSync("node", [cli, dir, "--write"], { encoding: "utf8" });
  assert.equal(result.status, 2);
  assert.match(result.stdout, /START_HERE\.md/);
  rmSync(dir, { recursive: true });
});

test("templates match START_HERE.md", () => {
  const result = spawnSync("node", [join(pkg, "scripts/sync-templates.js"), "--check"], { encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);
});
