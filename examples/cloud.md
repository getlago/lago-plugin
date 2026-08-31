# Lago Cloud integration example

Request: implement a Node service for monthly base subscription plus API-call usage.

Sequence: confirm US/EU region → discover existing service/config/test conventions → define customer/subscription authority → create billing adapter → validate deterministic `api_request:{request_id}` events with occurrence timestamps → add raw-body webhook verification/dedupe → run unit/integration fixtures and an offline money test.

Do not seed a generic demo into Lago Cloud, including a staging account. If a live demo is requested, run the same synthetic scenario on a dedicated isolated self-hosted Lago instance. Cloud validation is a separate, explicitly approved check of the user's real integration configuration and records.

Production remains gated until the exact workspace, records, billing impact, and rollback are approved.
