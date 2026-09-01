import json
import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/implementation/scripts"
FIXTURES = ROOT / "tests/fixtures"


def run(script: str, *args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *(str(arg) for arg in args)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class ScriptTests(unittest.TestCase):
    def test_public_repository_validator(self):
        result = run("validate_repo.py", ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "PASS")

    def test_valid_event(self):
        result = run("validate_event.py", FIXTURES / "event-valid.json")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_invalid_event(self):
        result = run("validate_event.py", FIXTURES / "event-invalid.json")
        self.assertEqual(result.returncode, 1)
        errors = json.loads(result.stdout)["errors"]
        self.assertIn("missing timestamp", errors)
        self.assertIn("transaction_id appears retry-unstable", errors)

    def test_money_test_passes_exact_decimal_equivalence(self):
        result = run(
            "money_test.py",
            FIXTURES / "money-expected.json",
            FIXTURES / "money-actual-pass.json",
            "--actual-source",
            FIXTURES / "lago-invoice-payload.json",
        )
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_money_test_reports_mismatch(self):
        result = run(
            "money_test.py",
            FIXTURES / "money-expected-fail.json",
            FIXTURES / "money-actual-pass.json",
            "--actual-source",
            FIXTURES / "lago-invoice-payload.json",
        )
        self.assertEqual(result.returncode, 1)
        fields = {item["field"] for item in json.loads(result.stdout)["mismatches"]}
        self.assertIn("total", fields)
        self.assertIn("expected_formula", fields)

    def test_extract_actual_is_tied_to_lago_payload(self):
        result = run("extract_actual.py", FIXTURES / "lago-invoice-payload.json")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(
            json.loads(result.stdout),
            json.loads((FIXTURES / "money-actual-pass.json").read_text(encoding="utf-8")),
        )

    def test_extract_actual_supports_current_usage_payload(self):
        result = run("extract_actual.py", FIXTURES / "lago-current-usage-payload.json")
        self.assertEqual(result.returncode, 0, result.stdout)
        actual = json.loads(result.stdout)
        self.assertEqual(actual["_evidence"]["source_kind"], "customer_usage")
        self.assertEqual(actual["quantity"], "21000")
        self.assertEqual(actual["total"], "0.37")
        self.assertEqual(actual["_basis"]["item_code"], "demo_ai_tokens")

    def test_extract_actual_rejects_mixed_quantity_dimensions(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = Path(directory) / "mixed.json"
            payload.write_text(
                json.dumps(
                    {
                        "customer_usage": {
                            "currency": "USD",
                            "amount_cents": 200,
                            "taxes_amount_cents": 0,
                            "total_amount_cents": 200,
                            "charges_usage": [
                                {"units": "1", "billable_metric": {"code": "seats"}},
                                {"units": "1", "billable_metric": {"code": "tokens"}},
                            ],
                        }
                    }
                ),
                encoding="utf-8",
            )
            result = run("extract_actual.py", payload)
        self.assertEqual(result.returncode, 1)
        self.assertIn("mixes multiple billable item codes", result.stdout)

    def test_extract_actual_returns_structured_size_failure(self):
        result = run(
            "extract_actual.py",
            FIXTURES / "lago-invoice-payload.json",
            "--max-bytes",
            1,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["status"], "FAIL")

    def test_extract_actual_uses_explicit_invoice_credits(self):
        result = run("extract_actual.py", FIXTURES / "lago-invoice-payload.json")
        self.assertEqual(result.returncode, 0, result.stdout)
        actual = json.loads(result.stdout)
        self.assertEqual(actual["credits"], "1")
        self.assertEqual(
            actual["_basis"]["credits"],
            "credit notes + prepaid credits + progressive-billing credits",
        )
        self.assertEqual(
            actual["_basis"]["credit_components"],
            {
                "credit_notes_amount_cents": "1",
                "prepaid_credit_amount_cents": "0",
                "progressive_billing_credit_amount_cents": "0",
            },
        )

    def test_extract_actual_rejects_missing_adjustment_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = json.loads(
                (FIXTURES / "lago-invoice-payload.json").read_text(encoding="utf-8")
            )
            del payload["invoice"]["prepaid_credit_amount_cents"]
            path = Path(directory) / "missing-adjustment.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = run("extract_actual.py", path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("prepaid_credit_amount_cents", result.stdout)

    def test_extract_actual_rejects_unlabeled_invoice_fees(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = json.loads(
                (FIXTURES / "lago-invoice-payload.json").read_text(encoding="utf-8")
            )
            del payload["invoice"]["fees"][0]["item"]
            path = Path(directory) / "unlabeled-fee.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = run("extract_actual.py", path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("no billable item code", result.stdout)

    def test_money_test_rejects_hand_written_actual(self):
        with tempfile.TemporaryDirectory() as directory:
            actual = Path(directory) / "actual.json"
            actual.write_text(
                (FIXTURES / "money-expected.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            result = run(
                "money_test.py",
                FIXTURES / "money-expected.json",
                actual,
                "--actual-source",
                FIXTURES / "lago-invoice-payload.json",
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("not hand-written", result.stdout)

    def test_money_test_rejects_modified_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            actual = Path(directory) / "actual.json"
            payload = json.loads(
                (FIXTURES / "money-actual-pass.json").read_text(encoding="utf-8")
            )
            payload["total"] = "999"
            actual.write_text(json.dumps(payload), encoding="utf-8")
            result = run(
                "money_test.py",
                FIXTURES / "money-expected.json",
                actual,
                "--actual-source",
                FIXTURES / "lago-invoice-payload.json",
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("differs from a fresh extraction", result.stdout)

    def test_money_test_requires_currency(self):
        payload = {"quantity": "1", "unit_price": "1", "subtotal": "1", "discounts": "0", "credits": "0", "tax": "0", "total": "1"}
        with tempfile.TemporaryDirectory() as directory:
            no_currency = Path(directory) / "money-no-currency.json"
            no_currency.write_text(json.dumps(payload), encoding="utf-8")
            result = run("money_test.py", no_currency, no_currency)
        self.assertEqual(result.returncode, 1)
        fields = {item["field"] for item in json.loads(result.stdout)["mismatches"]}
        self.assertIn("currency", fields)

    def test_money_test_rejects_float_negative_and_noncanonical_currency(self):
        cases = (
            ("unit_price", 0.25, "exact decimal string"),
            ("credits", "-1", "non-negative"),
            ("currency", "usd", "uppercase three-letter"),
        )
        for field, value, message in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                expected = json.loads(
                    (FIXTURES / "money-expected.json").read_text(encoding="utf-8")
                )
                expected[field] = value
                path = Path(directory) / "expected.json"
                path.write_text(json.dumps(expected), encoding="utf-8")
                result = run(
                    "money_test.py",
                    path,
                    FIXTURES / "money-actual-pass.json",
                    "--actual-source",
                    FIXTURES / "lago-invoice-payload.json",
                )
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn(message, result.stdout)

    def test_reconciliation_fails_on_empty_input(self):
        with tempfile.TemporaryDirectory() as directory:
            empty = Path(directory) / "reconcile-empty.csv"
            empty.write_text("external_id,amount,currency\n", encoding="utf-8")
            result = run("reconcile.py", FIXTURES / "reconcile-source.csv", empty)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["status"], "FAIL")

    def test_reconciliation_classifies_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.csv"
            source.write_text(
                "external_id,amount,currency\nA,1.00,USD\nA,2.00,USD\n",
                encoding="utf-8",
            )
            result = run("reconcile.py", source, FIXTURES / "reconcile-lago-pass.csv")
        self.assertEqual(result.returncode, 2, result.stdout)
        duplicates = [
            item
            for item in json.loads(result.stdout)["discrepancies"]
            if item["class"] == "duplicate key"
        ]
        self.assertEqual(duplicates[0]["side"], "source")

    def test_reconciliation_reports_missing_amount_column(self):
        with tempfile.TemporaryDirectory() as directory:
            invalid = Path(directory) / "invalid.csv"
            invalid.write_text("external_id,total,currency\nA,1.00,USD\n", encoding="utf-8")
            result = run("reconcile.py", invalid, FIXTURES / "reconcile-lago-pass.csv")
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing required column: amount", result.stdout)

    def test_reconciliation_returns_structured_size_failure(self):
        result = run(
            "reconcile.py",
            FIXTURES / "reconcile-source.csv",
            FIXTURES / "reconcile-lago-pass.csv",
            "--max-bytes",
            1,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["status"], "FAIL")

    def test_reconciliation_detects_currency_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            lago = Path(directory) / "lago.csv"
            lago.write_text(
                "external_id,amount,currency\nsynthetic_001,2.00,EUR\nsynthetic_002,5.00,USD\n",
                encoding="utf-8",
            )
            result = run("reconcile.py", FIXTURES / "reconcile-source.csv", lago)
        self.assertEqual(result.returncode, 2)
        classes = {item["class"] for item in json.loads(result.stdout)["discrepancies"]}
        self.assertIn("currency mismatch", classes)

    def test_reconciliation_reports_totals_and_accepts_utf8_bom(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.csv"
            source.write_text(
                "\ufeffexternal_id,amount,currency\nsynthetic_001,2.00,USD\nsynthetic_002,5.00,USD\n",
                encoding="utf-8",
            )
            result = run("reconcile.py", source, FIXTURES / "reconcile-lago-pass.csv")
        self.assertEqual(result.returncode, 0, result.stdout)
        counts = json.loads(result.stdout)["counts"]
        self.assertEqual(counts["source_totals_by_currency"], {"USD": "7"})
        self.assertEqual(counts["lago_totals_by_currency"], {"USD": "7"})

    def test_reconciliation_rejects_duplicate_headers_and_invalid_currency(self):
        cases = (
            (
                "external_id,amount,amount,currency\nA,1,1,USD\n",
                "duplicate columns",
            ),
            ("external_id,amount,currency\nA,1,US\n", "invalid currency"),
        )
        for content, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / "source.csv"
                source.write_text(content, encoding="utf-8")
                result = run("reconcile.py", source, FIXTURES / "reconcile-lago-pass.csv")
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn(message, result.stdout)

    def test_event_accepts_numeric_string_timestamp(self):
        with tempfile.TemporaryDirectory() as directory:
            event = Path(directory) / "event-string-timestamp.json"
            event.write_text(json.dumps({"event": {"transaction_id": "api_request:req_synthetic_002", "external_subscription_id": "sub_synthetic_001", "code": "api_requests", "timestamp": "1787702400", "properties": {"quantity": 1}}}), encoding="utf-8")
            result = run("validate_event.py", event)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_event_rejects_negative_and_string_quantities(self):
        base = {
            "transaction_id": "api_request:req_synthetic_003",
            "external_subscription_id": "sub_synthetic_001",
            "code": "api_requests",
            "timestamp": 1787702400,
        }
        with tempfile.TemporaryDirectory() as directory:
            negative = Path(directory) / "negative.json"
            string = Path(directory) / "string.json"
            negative.write_text(json.dumps({"event": {**base, "properties": {"quantity": -1}}}), encoding="utf-8")
            string.write_text(json.dumps({"event": {**base, "properties": {"quantity": "12"}}}), encoding="utf-8")
            negative_result = run("validate_event.py", negative)
            string_result = run("validate_event.py", string)
        self.assertEqual(negative_result.returncode, 1)
        self.assertIn("must be non-negative", negative_result.stdout)
        self.assertEqual(string_result.returncode, 1)
        self.assertIn("must be a number", string_result.stdout)

    def test_event_allows_explicit_negative_correction_property(self):
        with tempfile.TemporaryDirectory() as directory:
            correction = Path(directory) / "correction.json"
            correction.write_text(
                json.dumps({"event": {"transaction_id": "correction:1", "external_subscription_id": "sub_synthetic_001", "code": "api_requests", "timestamp": 1787702400, "properties": {"quantity": -1}}}),
                encoding="utf-8",
            )
            result = run(
                "validate_event.py",
                correction,
                "--allow-negative-property",
                "quantity",
            )
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_event_returns_structured_failure_for_bad_json(self):
        with tempfile.TemporaryDirectory() as directory:
            invalid = Path(directory) / "invalid.json"
            invalid.write_text("{", encoding="utf-8")
            result = run("validate_event.py", invalid)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["status"], "FAIL")

    def test_event_rejects_schema_type_and_precision_errors(self):
        base = {
            "transaction_id": "event:1",
            "external_subscription_id": "subscription:1",
            "code": "api_requests",
            "timestamp": 1787702400,
            "properties": {"region": "us"},
        }
        cases = (
            ({**base, "transaction_id": 123}, "transaction_id must be a string"),
            ({**base, "timestamp": 1787702400.5}, "integer or exact numeric string"),
            ({**base, "properties": {"region": ["us"]}}, "must be a string or number"),
            ({**base, "precise_total_amount_cents": 12.5}, "exact decimal string"),
            ({**base, "precise_total_amount_cents": "-1"}, "must be non-negative"),
        )
        for event, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "event.json"
                path.write_text(json.dumps({"event": event}), encoding="utf-8")
                result = run("validate_event.py", path)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn(message, result.stdout)

    def test_event_rejects_non_finite_json_constant(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "event.json"
            path.write_text(
                '{"event":{"transaction_id":"e:1","external_subscription_id":"s:1","code":"c","timestamp":1,"properties":{"quantity":NaN}}}',
                encoding="utf-8",
            )
            result = run("validate_event.py", path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("non-finite JSON value NaN", result.stdout)

    def test_reconciliation_passes(self):
        result = run("reconcile.py", FIXTURES / "reconcile-source.csv", FIXTURES / "reconcile-lago-pass.csv")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_reconciliation_classifies_differences(self):
        result = run("reconcile.py", FIXTURES / "reconcile-source.csv", FIXTURES / "reconcile-lago-diff.csv")
        self.assertEqual(result.returncode, 2)
        classes = {item["class"] for item in json.loads(result.stdout)["discrepancies"]}
        self.assertEqual(classes, {"amount mismatch", "missing in Lago", "missing in source"})

    def test_instant_demo_is_runnable_and_reconciles(self):
        result = run("run_demo.py", "--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        evidence = json.loads(result.stdout)
        self.assertEqual(evidence["mode"], "offline_example")
        self.assertEqual(evidence["events_accepted"], 4)
        self.assertTrue(evidence["duplicate_retry_ignored"])
        self.assertEqual(evidence["total_tokens"], 21_000)
        self.assertEqual(evidence["expected_total"], "0.37")
        self.assertEqual(evidence["actual_total"], "0.37")
        self.assertEqual(evidence["reconciliation_discrepancy"], "0.00")
        self.assertFalse(evidence["live_lago_contacted"])
        human = run("run_demo.py")
        self.assertEqual(human.returncode, 0, human.stdout + human.stderr)
        self.assertIn("You do not need to do anything", human.stdout)
        self.assertIn("Offline example complete", human.stdout)
        self.assertIn("expert mode", human.stdout)

    def test_demo_target_requires_loopback_port_and_dedicated_project(self):
        valid = run(
            "validate_demo_target.py",
            "http://127.0.0.1:39001/api/v1",
            "--compose-project",
            "lago-plugin-demo-test1",
        )
        self.assertEqual(valid.returncode, 0, valid.stdout)
        for url, project, message in (
            ("https://api.getlago.com", "lago-plugin-demo-test1", "remote targets"),
            ("http://localhost", "lago-plugin-demo-test1", "declare the dedicated local port"),
            ("http://localhost:39001", "lago", "lago-plugin-demo-<suffix>"),
        ):
            with self.subTest(url=url, project=project):
                result = run(
                    "validate_demo_target.py",
                    url,
                    "--compose-project",
                    project,
                )
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn(message, result.stdout)

    def test_release_integrity_detects_bundle_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "plugin.txt"
            source.write_text("reviewed\n", encoding="utf-8")
            manifest = root / "RELEASE-MANIFEST.json"
            created = run(
                "release_integrity.py",
                "create",
                root,
                "--output",
                manifest,
            )
            self.assertEqual(created.returncode, 0, created.stdout)
            checked = run(
                "release_integrity.py",
                "check",
                root,
                "--manifest",
                manifest,
            )
            self.assertEqual(checked.returncode, 0, checked.stdout)
            source.write_text("tampered\n", encoding="utf-8")
            drift = run(
                "release_integrity.py",
                "check",
                root,
                "--manifest",
                manifest,
            )
        self.assertEqual(drift.returncode, 1, drift.stdout)
        self.assertEqual(json.loads(drift.stdout)["changed"], ["plugin.txt"])

    def test_eval_suite_has_all_78_unique_cases(self):
        data = json.loads((ROOT / "evals/implementation/cases.json").read_text(encoding="utf-8"))
        cases = data["cases"]
        self.assertEqual(len(cases), 78)
        self.assertEqual(len({case["id"] for case in cases}), 78)
        self.assertTrue(all(case["signals"] for case in cases))

    def test_eval_suite_covers_first_run_workspace_failures(self):
        data = json.loads((ROOT / "evals/implementation/cases.json").read_text(encoding="utf-8"))
        ids = {case["id"] for case in data["cases"]}
        self.assertTrue({
            "content-only-folder",
            "empty-folder",
            "documentation-repository",
            "multiple-candidate-repositories",
            "monorepo-preflight",
            "expects-live-lago-access",
            "minimal-implement-prompt",
            "application-without-billing",
            "beginner-needs-primitives",
            "cloud-staging-demo-refusal",
            "canonical-per-token-demo",
            "greenfield-blueprint-first",
            "beginner-offline-walkthrough",
            "demo-is-not-production-ready",
            "ambiguous-help-start-no-app",
            "expert-mode-opt-out",
            "hand-written-actual-evidence",
            "official-doc-link-moved",
            "dry-run-approval-laundering",
            "remote-self-hosted-demo-target",
            "tampered-plugin-bundle",
            "premature-source-cancellation",
            "credential-presence-preflight",
        }.issubset(ids))

    def test_eval_suite_covers_field_replay_use_cases(self):
        data = json.loads((ROOT / "evals/implementation/cases.json").read_text(encoding="utf-8"))
        ids = {case["id"] for case in data["cases"]}
        self.assertTrue({
            "ai-value-credits",
            "ai-multimodal-filtered-pricing",
            "ai-prepaid-trial-and-purchase",
            "ai-greenfield-opportunity-scan",
            "ai-wallet-depletion-enforcement",
            "outcome-priced-agent",
            "chargebee-wallet-coexistence",
            "stripe-subscription-lago-metering",
            "wallet-top-up-modes",
            "wallet-metric-scope-and-priority",
            "wallet-tax-accounting-boundary",
            "fixed-fee-wallet-separation",
            "enterprise-overrides-multiple-entities",
            "annual-contract-monthly-usage",
            "plan-cadence-change",
            "pricing-backtest",
            "high-volume-wallet-events",
            "crm-erp-finance-handoff",
            "marketplace-payout-boundary",
        }.issubset(ids))

    def test_external_link_lister_finds_official_docs(self):
        result = run(
            "list_external_links.py",
            ROOT,
            "--domain",
            "docs.getlago.com",
            "--domain",
            "swagger.getlago.com",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("https://docs.getlago.com", result.stdout)
        self.assertIn("https://swagger.getlago.com/openapi.yaml", result.stdout)

    def test_runtime_skill_requires_activation_and_capability_boundary(self):
        skill = (ROOT / "skills/implementation/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Lago Billing Engineer loaded.", skill)
        self.assertIn("Mandatory first-run preflight", skill)
        self.assertIn("credentials are unnecessary for offline work", skill)
        self.assertIn("Ask only the next question", skill)
        discovery = (ROOT / "skills/implementation/references/discovery.md").read_text(encoding="utf-8")
        self.assertIn("No existing billing code is not a blocker.", discovery)
        primitives = (ROOT / "skills/implementation/references/primitives.md").read_text(encoding="utf-8")
        self.assertIn("Your application → Lago", primitives)
        self.assertIn("Never quiz the user", primitives)
        demo = (ROOT / "skills/implementation/references/demo.md").read_text(encoding="utf-8")
        self.assertIn("Never seed demo customers", demo)
        self.assertIn("including an account the user calls development, test, or staging", demo)
        canonical_demo = (ROOT / "examples/per-token-ai.md").read_text(encoding="utf-8")
        self.assertIn("The model names and prices are illustrative", canonical_demo)
        self.assertIn("$0.37", canonical_demo)
        guided = (ROOT / "skills/implementation/references/guided-experience.md").read_text(encoding="utf-8")
        self.assertIn("the billing blueprint", guided)
        self.assertIn("Offline example complete", guided)
        self.assertIn("You do not need to do anything", guided)
        self.assertIn("Gratification before intake", guided)
        use_cases = (ROOT / "skills/implementation/references/use-case-discovery.md").read_text(encoding="utf-8")
        self.assertIn("Opportunity scan", use_cases)
        self.assertIn("High-value AI-native patterns", use_cases)
        self.assertIn("application—not Lago—enforce", use_cases)
        self.assertIn("Do not assume Lago must replace the full billing stack", use_cases)
        self.assertIn("deliberate five-pattern check", use_cases)
        self.assertIn("money test match the recommended first candidate exactly", use_cases)
        events = (ROOT / "skills/implementation/references/events.md").read_text(encoding="utf-8")
        self.assertIn("customer identity and subscription identity distinct", events)
        self.assertIn("expert mode", skill)
        self.assertIn("guided mode", skill)
        self.assertIn("scripts/run_demo.py", skill)
        self.assertIn("never let `demo works` imply `ready for production`", skill)

    def test_manifest_identity_and_versions_match(self):
        codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        codex_marketplace = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        claude_marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(codex["name"], claude["name"])
        self.assertEqual(codex["version"], claude["version"])
        self.assertEqual(codex["name"], "lago")
        self.assertEqual(codex_marketplace["name"], "getlago")
        self.assertEqual(claude_marketplace["name"], "getlago")
        self.assertEqual(codex_marketplace["plugins"][0]["name"], "lago")
        self.assertEqual(claude_marketplace["plugins"][0]["name"], "lago")
        self.assertTrue(all(len(prompt) <= 128 for prompt in codex["interface"]["defaultPrompt"]))

    def test_archived_live_self_hosted_money_evidence(self):
        evidence = ROOT / "docs/release-evidence/v0.1.0-live-self-hosted"
        result = run(
            "money_test.py",
            evidence / "expected.json",
            evidence / "actual.json",
            "--actual-source",
            evidence / "lago-current-usage.json",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        metadata = json.loads((evidence / "run-metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["status"], "LIVE_SELF_HOSTED_USAGE_RETRIEVED")
        self.assertEqual(metadata["lago_version"], "v1.52.1")
        self.assertEqual(metadata["compose_project"], "lago-plugin-demo-v1521")
        self.assertEqual(metadata["target"], "http://127.0.0.1:13000/api/v1")
        self.assertEqual(metadata["duplicate_retry_http_status"], 422)
        self.assertFalse(metadata["payment_collection_enabled"])
        self.assertFalse(metadata["external_tax_enabled"])
        self.assertFalse(metadata["email_delivery_enabled"])

    def test_migration_ledger_tracks_cutover_and_rollback_boundaries(self):
        path = ROOT / "skills/implementation/templates/migration-ledger.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        self.assertTrue(rows)
        self.assertTrue(all(len(row) == len(rows[0]) for row in rows))
        for field in (
            "customer_or_cohort_scope",
            "billing_period_start",
            "billing_period_end",
            "source_owner_before",
            "target_owner_after",
            "cutover_at",
            "routing_state",
            "rollback_checkpoint",
        ):
            self.assertIn(field, rows[0])


if __name__ == "__main__":
    unittest.main()
