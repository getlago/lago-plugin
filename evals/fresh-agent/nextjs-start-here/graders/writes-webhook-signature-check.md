---
type: llm
focus: trace
---
Inspect the actual generated code and successful tool outputs, regardless of whether it was created with Write, Edit or a shell copy. PASS only if this requirement is implemented: The webhook route verifies X-Lago-Signature against the raw body before parsing. HMAC uses a dedicated HMAC secret, never the API key; JWT verifies RS256 against the Lago public key. FAIL if absent, only proposed, or unverifiable.
