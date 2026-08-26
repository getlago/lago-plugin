# Safety and production gates

Default to repository inspection, synthetic data, sandbox environments, read-only validation, dry runs, and reviewable diffs.

Get explicit approval immediately before any production Lago, Stripe, or Chargebee contact; creating/changing customers or subscriptions; sending events; creating/refreshing/finalizing/voiding/issuing invoices; applying credits/refunds; changing payment configuration or event routing; production migration/deployment; rotating credentials; or deleting/rewriting billing data.

Show before approval:

| Gate | Required detail |
| --- | --- |
| Target | provider, account/workspace, region, environment |
| Action | exact command/API operation and read/write nature |
| Scope | object types, selectors, estimated count |
| Billing impact | customers, usage, periods, invoices, payments |
| Infrastructure impact | services, downtime, migrations, capacity |
| Recovery | rollback/checkpoint/restore and stop condition |

Approval covers only the shown action. Reconfirm when target, scope, or impact changes.

Never expose credentials in commands, diffs, process listings, logs, fixtures, prompts, or docs. Use existing secret management and least privilege. Stop on detected production credentials in source and recommend rotation without printing the value.
