# Start here: usage-based billing with Lago

This page is for a coding agent, or a developer, with nothing installed. Follow it from top to bottom to add usage-based, per-token, per-API-call, seat-plus-usage, or prepaid-credit billing to an application with [Lago](https://www.getlago.com), the open-source billing and metering engine.

Lago runs as [Lago Cloud](https://getlago.com/docs/guide/lago-cloud) or [self-hosted](https://getlago.com/docs/guide/lago-self-hosted/docker). It does not process payments itself; you connect the payment provider you choose.

**Responsibilities.** The application owns product identity, durable usage records, event delivery, and access enforcement. Lago owns metering, pricing, credits, and invoices. Do not build a parallel rating engine, credit ledger, or invoice engine in the application.

## 1. See it work offline (30 seconds)

No account, key, Docker, or install is needed. Python 3.9 or later is enough.

```bash
git clone --depth 1 https://github.com/getlago/lago-plugin.git
python3 lago-plugin/skills/implementation/scripts/run_demo.py
```

The script follows one AI action from four token records and a retry to a duplicate-safe `$0.37` charge, `$0.20` of remaining included usage, and `$0.17` of overage. It writes no files and contacts no service. `--json` prints machine-readable evidence.

## 2. Configure

| Variable | Value | Rule |
| --- | --- | --- |
| `LAGO_API_URL` | `https://api.getlago.com` (US Cloud), `https://api.eu.getlago.com` (EU Cloud), or your self-hosted API origin such as `http://localhost:3000` | Required. Ask the user for the region; never guess it. Origin only: the code appends `/api/v1`. |
| `LAGO_API_KEY` | From the Lago UI, Developers section | Server-side secret. Never commit it, log it, or send it to a browser. |

Lago has no built-in sandbox. Each Lago account is one environment. Run synthetic tests against a dedicated self-hosted instance, not a production organization. Every live write to a production organization needs the user's explicit approval for that exact action.

## 3. Create the pricing once

Create a billable metric and a plan once per Lago organization, in the Lago UI or with the API. This example bills tokens at `$0.02` per 1,000 (a per-token price of `0.00002`), plus `$49` a month.

```bash
curl -sS -X POST "$LAGO_API_URL/api/v1/billable_metrics" \
  -H "Authorization: Bearer $LAGO_API_KEY" -H "Content-Type: application/json" \
  -d '{"billable_metric": {"name": "LLM tokens", "code": "llm_tokens", "aggregation_type": "sum_agg", "field_name": "tokens", "recurring": false}}'
# Copy billable_metric.lago_id from the response into the plan below.

curl -sS -X POST "$LAGO_API_URL/api/v1/plans" \
  -H "Authorization: Bearer $LAGO_API_KEY" -H "Content-Type: application/json" \
  -d '{"plan": {"name": "Pro", "code": "pro", "interval": "monthly", "amount_cents": 4900, "amount_currency": "USD", "pay_in_advance": true,
       "charges": [{"billable_metric_id": "<billable_metric.lago_id>", "charge_model": "standard", "pay_in_advance": false, "properties": {"amount": "0.00002"}}]}}'
```

Prices are decimal strings. Plan fees are integer cents. `count_agg`, `max_agg`, and `latest_agg` require `recurring: false`. For seats that carry across periods, use `unique_count_agg` with `recurring: true` ([recurring vs metered](https://getlago.com/docs/guide/billable-metrics/recurring-vs-metered)).

## 4. The rules that keep billing correct

1. **`transaction_id` comes from a durable source record**, such as the row ID of the usage record the application already stores. Never generate a random ID per send or per retry.
2. **Send an explicit `timestamp`** equal to when the usage happened, and resend it unchanged on retry. On Lago's ClickHouse pipeline, uniqueness is `transaction_id` plus `timestamp`, so a retry with a new timestamp bills twice.
3. **Customer and subscription IDs are different things.** `external_customer_id` is the paying account. `external_subscription_id` is that account's enrollment in a plan. Store both.
4. **Activate the subscription before sending usage.** Events timestamped before the subscription starts are stored but not billed.
5. **A duplicate is not a success.** On the Postgres pipeline, a reused `transaction_id` returns HTTP 422 with `value_already_exist`. Mark the record delivered only after matching it to the stored event. Any other 422 is a contract error.
6. **Retry only transient failures**: network errors, timeouts, 429, and 5xx, with bounded backoff and jitter.
7. **Verify webhook signatures against the raw request body**, deduplicate on `X-Lago-Unique-Key`, and acknowledge with 2xx only after storing the webhook durably.
8. **An accepted event is not a billed event.** Check current usage before claiming that usage was billed.

## 5. Node.js / TypeScript

Node 18 or later. No dependencies: it uses `fetch` and `node:crypto`. Put it behind one billing module in the application.

```ts file=lago-billing.ts
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
    try {
      response = await fetch(`${config.apiUrl}/api/v1${path}`, {
        method,
        headers: { Authorization: `Bearer ${config.apiKey}`, "Content-Type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: AbortSignal.timeout(config.timeoutMs ?? 10_000),
      });
    } catch (error) {
      if (attempt >= attempts) throw error;
      await sleep(Math.min(8_000, 250 * 2 ** attempt) * Math.random());
      continue;
    }
    const text = await response.text();
    const json = text ? JSON.parse(text) : null;
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
export function createSubscription(config: LagoConfig, s: { id: string; customerId: string; planCode: string }) {
  return lago(config, "POST", "/subscriptions", {
    subscription: { external_id: s.id, external_customer_id: s.customerId, plan_code: s.planCode },
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

// Prepaid credits: ongoing_balance_cents already subtracts current usage.
export async function prepaidBalanceCents(config: LagoConfig, customerId: string): Promise<number> {
  const { wallets } = await lago(config, "GET", `/wallets?${new URLSearchParams({ external_customer_id: customerId })}`);
  return (wallets as any[]).filter((w) => w.status === "active").reduce((sum, w) => sum + w.ongoing_balance_cents, 0);
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
```

Webhook route for the Next.js App Router. Swap `inbox` for the application's own durable storage with a unique constraint on the key.

```ts file=webhook-route.ts
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
```

In `app/api/lago/webhooks/route.ts`: `export const POST = makeWebhookHandler(inbox, enqueue);`.

## 6. Python

Python 3.9 or later. Standard library for the API. [PyJWT](https://pyjwt.readthedocs.io) with `cryptography` (`pip install "pyjwt[crypto]"`) only if webhooks use the default JWT signature.

```python file=lago_billing.py
import base64
import hashlib
import hmac
import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime


class LagoError(Exception):
    def __init__(self, status, body):
        super().__init__(f"Lago API error {status}")
        self.status, self.body = status, body


class Lago:
    def __init__(self, api_url=None, api_key=None, timeout=10, max_retries=4):
        self.api_url = (api_url or os.environ["LAGO_API_URL"]).rstrip("/")
        self.api_key = api_key or os.environ["LAGO_API_KEY"]
        self.timeout, self.max_retries = timeout, max_retries

    def _request(self, method, path, body=None):
        data = None if body is None else json.dumps(body).encode()
        for attempt in range(1, self.max_retries + 2):
            request = urllib.request.Request(
                f"{self.api_url}/api/v1{path}", data=data, method=method,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    text = response.read()
                    return json.loads(text) if text else None
            except urllib.error.HTTPError as error:
                text = error.read()
                payload = json.loads(text) if text else None
                if (error.code != 429 and error.code < 500) or attempt > self.max_retries:
                    raise LagoError(error.code, payload) from None
            except (urllib.error.URLError, TimeoutError):
                if attempt > self.max_retries:
                    raise
            time.sleep(random.uniform(0, min(8, 0.25 * 2 ** attempt)))

    def upsert_customer(self, account_id, name, currency, email=None):
        # Upsert: Lago updates the customer when external_id already exists.
        customer = {"external_id": account_id, "name": name, "email": email, "currency": currency}
        return self._request("POST", "/customers", {"customer": {k: v for k, v in customer.items() if v is not None}})

    def create_subscription(self, subscription_id, customer_id, plan_code):
        # external_id is the subscription's own durable ID, never the customer ID.
        return self._request("POST", "/subscriptions", {"subscription": {
            "external_id": subscription_id, "external_customer_id": customer_id, "plan_code": plan_code}})

    def send_usage(self, record_id, subscription_id, metric_code, occurred_at: datetime, properties):
        """record_id and occurred_at come from the durable usage record and never change on retry."""
        try:
            self._request("POST", "/events", {"event": {
                "transaction_id": record_id,
                "external_subscription_id": subscription_id,
                "code": metric_code,
                "timestamp": f"{occurred_at.timestamp():.3f}",
                "properties": properties,
            }})
            return "accepted"
        except LagoError as error:
            details = (error.body or {}).get("error_details") or {}
            if error.status == 422 and "value_already_exist" in details.get("transaction_id", []):
                return "duplicate"  # reconcile against the stored event before marking delivered
            raise

    def current_usage(self, customer_id, subscription_id):
        query = urllib.parse.urlencode({"external_subscription_id": subscription_id})
        path = f"/customers/{urllib.parse.quote(customer_id, safe='')}/current_usage?{query}"
        return self._request("GET", path)["customer_usage"]

    def entitlement(self, subscription_id, feature_code):
        """The application enforces access; Lago is the source of the plan's features and limits."""
        path = f"/subscriptions/{urllib.parse.quote(subscription_id, safe='')}/entitlements"
        for feature in self._request("GET", path)["entitlements"]:
            if feature["code"] == feature_code:
                return {"enabled": True, "privileges": {p["code"]: p["value"] for p in feature["privileges"]}}
        return {"enabled": False, "privileges": {}}

    def prepaid_balance_cents(self, customer_id):
        """ongoing_balance_cents already subtracts current usage."""
        query = urllib.parse.urlencode({"external_customer_id": customer_id})
        wallets = self._request("GET", f"/wallets?{query}")["wallets"]
        return sum(w["ongoing_balance_cents"] for w in wallets if w["status"] == "active")

    def webhook_public_key(self):
        """The JWT public key is PEM, base64-encoded. Fetch it once and cache it."""
        return base64.b64decode(self._request("GET", "/webhooks/json_public_key")["webhook"]["public_key"]).decode()


def verify_webhook(raw_body: bytes, headers, issuer, public_key_pem=None, hmac_key=None):
    """raw_body must be the exact request bytes. Never re-serialize parsed JSON."""
    signature = headers.get("X-Lago-Signature", "")
    algorithm = headers.get("X-Lago-Signature-Algorithm")
    if algorithm == "jwt" and public_key_pem:
        import jwt  # PyJWT

        claims = jwt.decode(signature, public_key_pem, algorithms=["RS256"], issuer=issuer, options={"require": ["iss"]})
        if claims.get("data") != raw_body.decode():
            raise ValueError("invalid webhook signature")
    elif algorithm == "hmac" and hmac_key:
        expected = base64.b64encode(hmac.new(hmac_key.encode(), raw_body, hashlib.sha256).digest()).decode()
        if not hmac.compare_digest(expected, signature):
            raise ValueError("invalid webhook signature")
    else:
        raise ValueError("unsupported or unconfigured webhook signature algorithm")
    return json.loads(raw_body)
```

A FastAPI webhook route. The same shape works in Flask or Django: read the raw body, verify, store under the unique key, then acknowledge.

```python
from fastapi import FastAPI, Request, Response

app = FastAPI()
lago = Lago()
public_key_pem = None

@app.post("/lago/webhooks")
async def lago_webhook(request: Request):
    global public_key_pem
    public_key_pem = public_key_pem or lago.webhook_public_key()
    raw_body = await request.body()
    try:
        payload = verify_webhook(raw_body, request.headers, issuer=lago.api_url,
                                 public_key_pem=public_key_pem, hmac_key=os.environ.get("LAGO_WEBHOOK_HMAC_KEY"))
    except Exception:
        return Response(status_code=401)
    unique_key = request.headers.get("X-Lago-Unique-Key")
    if not unique_key:
        return Response(status_code=400)
    if inbox.insert_if_new(unique_key, payload):  # your durable storage, unique constraint on the key
        enqueue(unique_key)  # process asynchronously
    return Response(status_code=204)
```

## 7. Wire it into the application

1. **Signup or billing activation:** `upsertCustomer`, then `createSubscription` with a subscription ID the application stores.
2. **Every billable action:** write the usage record to the application database first, then send it from a worker. Mark it delivered on `accepted`. Reconcile `duplicate` against the stored event.
3. **Before an expensive action:** call `entitlement` or `prepaidBalanceCents` and cache the answer briefly. The application decides whether to allow the action.
4. **Webhooks:** handle `invoice.created`, `wallet.depleted_ongoing_balance`, and `subscription.terminated` asynchronously ([webhook types](https://getlago.com/docs/api-reference/webhooks/messages)).

## 8. Verify before calling it done

- **Offline:** unit-test that retries reuse the same `transaction_id` and `timestamp`. Test that a 422 duplicate is not counted as success. Test that a tampered webhook body is rejected.
- **Money:** calculate the expected amount by hand. For 120,000 tokens at `0.00002`, that is `$2.40` on top of the `$49` plan fee. Compare it with `currentUsage` on a dedicated test instance.
- **Replay:** send the same record twice and confirm `units` did not increase.
- **Stage the result:** an offline test, a live test on a dedicated instance, and production readiness are three different claims. State which one you reached.

## Go further

- Install the Lago plugin for Claude Code or Codex for guided design, migrations from Stripe Billing or Chargebee, reconciliation, and money tests: [install](https://github.com/getlago/lago-plugin#install).
- [Lago API reference](https://getlago.com/docs/api-reference/intro), [OpenAPI](https://swagger.getlago.com/openapi.yaml), [event ingestion](https://getlago.com/docs/guide/events/ingesting-usage), [webhook signatures](https://getlago.com/docs/api-reference/webhooks/format---signature), [entitlements](https://getlago.com/docs/guide/entitlements), [wallets](https://getlago.com/docs/guide/wallet-and-prepaid-credits/overview).
