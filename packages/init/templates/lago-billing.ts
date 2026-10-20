import { createHmac, timingSafeEqual, verify } from "node:crypto";

export type LagoConfig = { apiUrl: string; apiKey: string; timeoutMs?: number; maxRetries?: number };

export class LagoError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, body: unknown) {
    super(`Lago API error ${status}`);
    this.status = status;
    this.body = body;
  }
}

export function configFromEnv(): LagoConfig {
  const apiUrl = process.env.LAGO_API_URL;
  const apiKey = process.env.LAGO_API_KEY;
  if (!apiUrl || !apiKey) throw new Error("LAGO_API_URL and LAGO_API_KEY are required");
  return { apiUrl: apiUrl.replace(/\/+$/, ""), apiKey };
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

async function lago(config: LagoConfig, method: string, path: string, body?: unknown): Promise<any> {
  const attempts = (config.maxRetries ?? 4) + 1;
  for (let attempt = 1; ; attempt++) {
    let response: Response;
    let text: string;
    try {
      response = await fetch(`${config.apiUrl}/api/v1${path}`, {
        method,
        redirect: "manual", // Never forward credentials or repeat a mutation through a redirect.
        headers: { Authorization: `Bearer ${config.apiKey}`, "Content-Type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: AbortSignal.timeout(config.timeoutMs ?? 10_000),
      });
      text = await response.text();
    } catch (error) {
      if (attempt >= attempts) throw error;
      await sleep(Math.min(8_000, 250 * 2 ** attempt) * Math.random());
      continue;
    }
    let json: any = null;
    try { json = text ? JSON.parse(text) : null; } catch {
      if (response.ok) throw new Error("Invalid JSON from Lago");
      // Proxies can return HTML for transient failures. Classify by status below.
    }
    if (response.ok) return json;
    const transient = response.status === 429 || response.status >= 500;
    if (!transient || attempt >= attempts) throw new LagoError(response.status, json);
    await sleep(Math.min(8_000, 250 * 2 ** attempt) * Math.random());
  }
}

// Upsert: Lago updates the customer when external_id already exists.
export function upsertCustomer(config: LagoConfig, account: { id: string; name: string; email?: string; currency: string }) {
  return lago(config, "POST", "/customers", {
    customer: { external_id: account.id, name: account.name, email: account.email, currency: account.currency },
  });
}

// external_id is the subscription's own durable ID, never the customer ID.
export function createSubscription(config: LagoConfig, s: { id: string; customerId: string; planCode: string; startsAt: Date }) {
  return lago(config, "POST", "/subscriptions", {
    subscription: { external_id: s.id, external_customer_id: s.customerId, plan_code: s.planCode,
      billing_time: "anniversary", subscription_at: s.startsAt.toISOString() },
  });
}

export type UsageRecord = {
  id: string; // durable source record ID, reused on every retry
  subscriptionId: string;
  metricCode: string;
  occurredAt: Date; // stored with the record, reused on every retry
  properties: Record<string, string | number>;
};

export async function sendUsage(config: LagoConfig, record: UsageRecord): Promise<"accepted" | "duplicate"> {
  try {
    await lago(config, "POST", "/events", {
      event: {
        transaction_id: record.id,
        external_subscription_id: record.subscriptionId,
        code: record.metricCode,
        timestamp: (record.occurredAt.getTime() / 1000).toFixed(3),
        properties: record.properties,
      },
    });
    return "accepted";
  } catch (error) {
    const details = error instanceof LagoError ? (error.body as any)?.error_details : undefined;
    if (error instanceof LagoError && error.status === 422 && details?.transaction_id?.includes("value_already_exist")) {
      return "duplicate"; // reconcile against the stored event before marking delivered
    }
    throw error;
  }
}

export async function currentUsage(config: LagoConfig, customerId: string, subscriptionId: string) {
  const query = new URLSearchParams({ external_subscription_id: subscriptionId });
  const { customer_usage } = await lago(config, "GET", `/customers/${encodeURIComponent(customerId)}/current_usage?${query}`);
  return customer_usage as { amount_cents: number; currency: string; charges_usage: { units: string; amount_cents: number; billable_metric: { code: string } }[] };
}

// Entitlements: the application enforces access; Lago is the source of the plan's features and limits.
export async function entitlement(config: LagoConfig, subscriptionId: string, featureCode: string) {
  const { entitlements } = await lago(config, "GET", `/subscriptions/${encodeURIComponent(subscriptionId)}/entitlements`);
  const feature = (entitlements as any[]).find((e) => e.code === featureCode);
  if (!feature) return { enabled: false, privileges: {} as Record<string, unknown> };
  return { enabled: true, privileges: Object.fromEntries(feature.privileges.map((p: any) => [p.code, p.value])) };
}

// Advisory snapshot, NOT a reservation or permission to spend. The caller supplies the charge context.
export async function prepaidBalanceCents(config: LagoConfig, customerId: string,
  context: { currency: string; feeType: "charge" | "subscription"; metricCode?: string }) {
  if (!/^[A-Z]{3}$/.test(context.currency) || !["charge", "subscription"].includes(context.feeType) ||
      (context.feeType === "charge" && !context.metricCode)) {
    throw new Error("Explicit currency and charge metric are required");
  }
  let amountCents = 0;
  for (let page = 1; ; page++) {
    const query = new URLSearchParams({ external_customer_id: customerId, page: String(page), per_page: "100" });
    const { wallets, meta } = await lago(config, "GET", `/wallets?${query}`);
    if (!Number.isSafeInteger(meta?.total_pages) || meta.total_pages < 0 || meta.total_pages > 1000) {
      throw new Error("Invalid wallet pagination; balance unavailable");
    }
    for (const w of wallets) {
      if (w.status !== "active" || w.currency !== context.currency) continue;
      const limits = w.applies_to ?? {};
      if (limits.fee_types?.length && !limits.fee_types.includes(context.feeType)) continue;
      if (limits.billable_metric_codes?.length &&
          (context.feeType !== "charge" || !limits.billable_metric_codes.includes(context.metricCode))) continue;
      if (!Number.isSafeInteger(w.ongoing_balance_cents)) throw new Error("Invalid wallet amount");
      amountCents += w.ongoing_balance_cents;
      if (!Number.isSafeInteger(amountCents)) throw new Error("Wallet total exceeds safe integer precision");
    }
    if (page >= meta.total_pages) break;
  }
  return { amountCents, currency: context.currency, advisory: true as const };
}

// The JWT public key is PEM, base64-encoded. Fetch it once and cache it.
export async function webhookPublicKey(config: LagoConfig): Promise<string> {
  const { webhook } = await lago(config, "GET", "/webhooks/json_public_key");
  return Buffer.from(webhook.public_key, "base64").toString("utf8");
}

export type WebhookKeys = { issuer: string; publicKeyPem?: string; hmacKey?: string };

// rawBody must be the exact request bytes. Never re-serialize parsed JSON.
export function verifyWebhook(rawBody: string, headers: Headers, keys: WebhookKeys): any {
  const signature = headers.get("x-lago-signature") ?? "";
  const algorithm = headers.get("x-lago-signature-algorithm");
  if (algorithm === "jwt" && keys.publicKeyPem) {
    const [header, payload, sig] = signature.split(".");
    if (!header || !payload || !sig) throw new Error("malformed webhook JWT");
    if (JSON.parse(Buffer.from(header, "base64url").toString()).alg !== "RS256") throw new Error("unexpected JWT algorithm");
    const valid = verify("RSA-SHA256", Buffer.from(`${header}.${payload}`), keys.publicKeyPem, Buffer.from(sig, "base64url"));
    const claims = JSON.parse(Buffer.from(payload, "base64url").toString());
    if (!valid || claims.iss !== keys.issuer || claims.data !== rawBody) throw new Error("invalid webhook signature");
  } else if (algorithm === "hmac" && keys.hmacKey) {
    const expected = createHmac("sha256", keys.hmacKey).update(rawBody).digest();
    const received = Buffer.from(signature, "base64");
    if (received.length !== expected.length || !timingSafeEqual(received, expected)) throw new Error("invalid webhook signature");
  } else {
    throw new Error("unsupported or unconfigured webhook signature algorithm");
  }
  return JSON.parse(rawBody);
}
