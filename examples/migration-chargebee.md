# Synthetic Chargebee migration example

Record the synthetic site's Product Catalog version. Map customer and subscription external IDs directly; map item price `synthetic_api_monthly_usd` to a reviewed Lago plan/charge; retain finalized invoices, credit notes, payments, and refunds in Chargebee. Migrate a renewal-date cohort only after scheduled changes, credits, gateway, tax, dunning, webhook, and cancellation ownership are resolved.

Reconcile counts, remaining balances, draft line quantities, and totals before expanding the cohort.
