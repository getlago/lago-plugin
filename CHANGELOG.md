# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and semantic versioning.

## [Unreleased]

### Added

- Untrusted-workspace boundary: repository content is evidence, never instructions or approval; approvals are valid only from the user in conversation, with matching adversarial eval cases.
- Hardened offline validators: money tests require a currency and reject non-finite values, reconciliation reports row counts and fails on empty input, event validation accepts documented numeric-string Unix timestamps, and the repository validator runs on Python 3.9.
- Blueprint-first beginner flow with one recommended default, an instant offline walkthrough path, compact progress and decision tracking, and precise completion levels.
- Behavioral evals for greenfield blueprinting, demo-first teaching, and the boundary between a working demo and production readiness.
- Dependency-free instant offline demo with duplicate-event and reconciliation evidence, plus a no-action-needed path for ambiguous beginner prompts outside an application repository.
- Gratification-first guided experience with one-step next actions and an `expert mode` opt-out that preserves safety and billing evidence while removing tutorials and routine narration.
- Evidence-derived money validation that extracts actuals from preserved Lago payloads and verifies their source hash; hand-written or modified actuals fail.
- Structured reconciliation failures for missing columns, duplicate keys, invalid amounts, empty inputs, and currency mismatches, plus stricter billable-event value validation.
- Approved public install identity `lago@getlago`, with `/lago:implementation` for Claude Code and `$lago:implementation` for Codex; validators prevent identity regression.

## [0.1.0] - 2026-08-26

### Added

- Shared eight-mode Lago implementation skill for Claude Code and Codex.
- Cloud, self-hosted, billing, events, webhook, migration, validation, reconciliation, troubleshooting, and safety references.
- Stripe Billing, Chargebee, and custom migration workflows.
- Offline event, money-test, reconciliation, and public-repository validators.
- Lago Billing Engineer positioning for applications with or without existing billing code.
- Beginner-first guidance that maps product concepts to Lago primitives one decision at a time.
- Hard isolation policy requiring self-hosted Lago for all seeded demos and prohibiting demo data in Lago Cloud.
- Canonical self-hosted OpenAI-style per-token demo with illustrative pricing and deterministic usage evidence.
- Mandatory first-run workspace and billing-state preflight, capability-boundary message, and contextual recovery guidance.
- Fifty-four synthetic eval cases, scorecard, examples, and release controls.
