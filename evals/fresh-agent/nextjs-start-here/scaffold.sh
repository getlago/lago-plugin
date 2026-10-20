#!/usr/bin/env bash
# Minimal Next.js App Router app with one billable LLM action and no billing.
set -euo pipefail
mkdir -p app/api/generate lib
cat > package.json <<'JSON'
{"name": "acme-ai", "private": true, "scripts": {"dev": "next dev"},
 "dependencies": {"next": "15.5.4", "react": "19.1.1", "react-dom": "19.1.1"},
 "devDependencies": {"typescript": "5.9.3", "@types/node": "24.6.0", "@types/react": "19.1.15"}}
JSON
cat > tsconfig.json <<'JSON'
{"compilerOptions": {"strict": true, "module": "esnext", "moduleResolution": "bundler", "jsx": "preserve", "target": "es2022",
 "paths": {"@/*": ["./*"]}}}
JSON
cat > app/layout.tsx <<'TSX'
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html><body>{children}</body></html>;
}
TSX
echo 'export default function Page() { return <main>Acme AI summaries</main>; }' > app/page.tsx
cat > lib/db.ts <<'TS'
// Stand-in for the app's database.
export type Workspace = { id: string; name: string; email: string; plan: "free" | "pro" };
export type Generation = { id: string; workspaceId: string; model: string; inputTokens: number; outputTokens: number; createdAt: Date };
export const db = {
  workspaces: new Map<string, Workspace>(),
  generations: new Map<string, Generation>(),
};
TS
cat > lib/llm.ts <<'TS'
// Stand-in for the LLM provider call.
export async function summarize(text: string) {
  return { summary: text.slice(0, 80), model: "gpt-4.1-mini", usage: { input_tokens: Math.ceil(text.length / 4), output_tokens: 20 } };
}
TS
cat > app/api/generate/route.ts <<'TS'
import { db } from "@/lib/db";
import { summarize } from "@/lib/llm";

export async function POST(request: Request) {
  const { workspaceId, text } = await request.json();
  const result = await summarize(text);
  const generation = {
    id: crypto.randomUUID(),
    workspaceId,
    model: result.model,
    inputTokens: result.usage.input_tokens,
    outputTokens: result.usage.output_tokens,
    createdAt: new Date(),
  };
  db.generations.set(generation.id, generation);
  return Response.json({ summary: result.summary });
}
TS
