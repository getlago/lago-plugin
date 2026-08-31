# Synthetic Stripe migration example

Map `cus_synthetic_001` to Lago external customer `cus_synthetic_001` and `sub_synthetic_001` to the same Lago external subscription ID. Keep finalized Stripe invoices read-only. Route one renewal cohort at a billing boundary, preserve each durable usage source ID as the Lago transaction ID, and compare Stripe/source expectations with Lago drafts for one full representative cycle.

The cutover gate fails if any customer-period or usage route can be invoiced by both systems.
