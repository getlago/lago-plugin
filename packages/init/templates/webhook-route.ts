import { configFromEnv, verifyWebhook, webhookPublicKey } from "./lago-billing";

export type WebhookInbox = { insertIfNew(uniqueKey: string, payload: unknown): Promise<boolean> };

let publicKeyPem: string | undefined;

export function makeWebhookHandler(inbox: WebhookInbox, enqueue: (uniqueKey: string) => Promise<void>) {
  return async function POST(request: Request): Promise<Response> {
    const config = configFromEnv();
    publicKeyPem ??= await webhookPublicKey(config);
    const rawBody = await request.text();
    let payload: unknown;
    try {
      // The JWT issuer is the Lago instance's API URL.
      payload = verifyWebhook(rawBody, request.headers, { issuer: config.apiUrl, publicKeyPem, hmacKey: process.env.LAGO_WEBHOOK_HMAC_KEY });
    } catch {
      return new Response("invalid signature", { status: 401 });
    }
    const uniqueKey = request.headers.get("x-lago-unique-key");
    if (!uniqueKey) return new Response("missing unique key", { status: 400 });
    if (await inbox.insertIfNew(uniqueKey, payload)) await enqueue(uniqueKey); // process asynchronously
    return new Response(null, { status: 204 }); // only after durable storage
  };
}
