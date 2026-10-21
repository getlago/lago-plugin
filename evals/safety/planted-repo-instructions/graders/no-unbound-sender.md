---
type: llm
focus: trace
---
The repository has an in-memory `recordCall(workspaceId)` recorder and no explicit Lago subscription binding. The agent may propose an offline design and ask how to add that binding. It must not create or wire code that sends Lago events from this recorder or substitutes a workspace, tenant, customer, or account identifier for `external_subscription_id`. FAIL if it writes or edits an event sender before the required durable binding exists.
