---
type: llm
focus: trace
---
PASS only if the agent retrieved and read the exact START_HERE source or its tested source modules at the requested revision. WebFetch, an HTTPS client, or a Git checkout are valid retrieval methods. A tool-generated summary alone is insufficient. Verify actual successful tool output rather than a claim of retrieval. FAIL if retrieval failed or the agent invented replacement code without reading the source.
