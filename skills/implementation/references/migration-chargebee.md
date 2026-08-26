# Chargebee migration

First identify Chargebee Product Catalog version, site, and environment. Inspect customers; products/items/plans/price points; subscriptions and scheduled changes; add-ons/one-time/metered charges; coupons; trials; contracts/commitments; credits/promotional balances; invoices/credit notes/payments/refunds; tax; gateways; dunning; billing dates/calendar/currency; custom fields/metadata; webhooks; revenue-recognition/accounting/reporting dependencies.

Stable mappings:

- Chargebee customer ID → Lago external customer ID
- Chargebee subscription ID → Lago external subscription ID
- Product/item/price identifier → reviewed Lago plan/charge mapping
- Durable source usage ID → Lago transaction ID
- Invoice/credit-note ID → reconciliation reference

Evaluate new-only, phased cohort, renewal-date, parallel, and full-cutover strategies. Default to retaining finalized financial documents and audit records in Chargebee. Do not assume similarly named fields behave alike.

The cutover plan must assign ownership for catalog freeze, customer/subscription sync, event routing, webhooks, payment gateway, dunning, invoices, credits/balances, scheduled changes, cancellations, reconciliation, rollback, and the Chargebee read-access period. One system owns each customer and billing period.

Sources: [Chargebee API](https://apidocs.chargebee.com/docs/api), [Product Catalog](https://www.chargebee.com/docs/billing/2.0/product-catalog/product-catalog), [Lago API](https://docs.getlago.com/api-reference/intro).
