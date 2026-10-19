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
