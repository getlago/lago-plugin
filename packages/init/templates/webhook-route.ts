import { configFromEnv, verifyWebhook, webhookPublicKey } from "./lago-billing";

export type WebhookInbox = { storePending(uniqueKey: string, payload: unknown): Promise<void> };

let publicKeyPem: string | undefined;

export function makeWebhookHandler(inbox: WebhookInbox) {
  return async function POST(request: Request): Promise<Response> {
    const config = configFromEnv();
    if (request.headers.get("x-lago-signature-algorithm") === "jwt") {
      publicKeyPem ??= await webhookPublicKey(config);
    }
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
    await inbox.storePending(uniqueKey, payload); // worker polls pending rows, including after a crash
    return new Response(null, { status: 204 }); // only after durable storage
  };
}
