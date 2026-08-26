# Synthetic Lago Cloud example

Request: implement a Node service for monthly base subscription plus API-call usage.

Sequence: confirm US/EU region → discover existing service/config/test conventions → define customer/subscription authority → create billing adapter → validate deterministic `api_request:{request_id}` events with occurrence timestamps → add raw-body webhook verification/dedupe → run unit/integration fixtures → create an authorized sandbox customer/subscription/events → compare the draft invoice with the independent money test.

Production remains gated until the exact workspace, records, billing impact, and rollback are approved.
