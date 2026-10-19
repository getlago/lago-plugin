// Generate templates/ from the code blocks in START_HERE.md, the single source of truth.
// `--check` exits 1 when the committed templates have drifted.
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const startHere = join(here, "../../../START_HERE.md");
const templates = join(here, "../templates");

export function extractBlocks(markdown) {
  const blocks = {};
  for (const match of markdown.matchAll(/^```\w+ file=([\w.-]+)\n([\s\S]*?)^```$/gm)) blocks[match[1]] = match[2];
  return blocks;
}

const blocks = extractBlocks(readFileSync(startHere, "utf8"));
const check = process.argv.includes("--check");
let drift = false;
for (const [name, body] of Object.entries(blocks)) {
  const target = join(templates, name);
  if (check) {
    if (!existsSync(target) || readFileSync(target, "utf8") !== body) {
      console.error(`template drift: ${name}`);
      drift = true;
    }
  } else {
    writeFileSync(target, body);
  }
}
process.exit(drift ? 1 : 0);
