import json
import subprocess
import sys
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
        result = run("money_test.py", FIXTURES / "money-expected.json", FIXTURES / "money-actual-pass.json")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_money_test_reports_mismatch(self):
        result = run("money_test.py", FIXTURES / "money-expected.json", FIXTURES / "money-actual-fail.json")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["mismatches"][0]["field"], "total")

    def test_money_test_requires_currency(self):
        payload = {"quantity": "1", "unit_price": "1", "subtotal": "1", "discounts": "0", "credits": "0", "tax": "0", "total": "1"}
        no_currency = FIXTURES / "money-no-currency.json"
        no_currency.write_text(json.dumps(payload), encoding="utf-8")
        try:
            result = run("money_test.py", no_currency, no_currency)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["mismatches"][0]["field"], "currency")
        finally:
            no_currency.unlink()

    def test_reconciliation_fails_on_empty_input(self):
        empty = FIXTURES / "reconcile-empty.csv"
        empty.write_text("external_id,amount\n", encoding="utf-8")
        try:
            result = run("reconcile.py", FIXTURES / "reconcile-source.csv", empty)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["status"], "FAIL")
        finally:
            empty.unlink()

    def test_event_accepts_numeric_string_timestamp(self):
        event = FIXTURES / "event-string-timestamp.json"
        event.write_text(json.dumps({"event": {"transaction_id": "api_request:req_synthetic_002", "external_subscription_id": "sub_synthetic_001", "code": "api_requests", "timestamp": "1787702400", "properties": {"quantity": 1}}}), encoding="utf-8")
        try:
            result = run("validate_event.py", event)
            self.assertEqual(result.returncode, 0, result.stdout)
        finally:
            event.unlink()

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

    def test_eval_suite_has_all_52_unique_cases(self):
        data = json.loads((ROOT / "evals/implementation/cases.json").read_text(encoding="utf-8"))
        cases = data["cases"]
        self.assertEqual(len(cases), 52)
        self.assertEqual(len({case["id"] for case in cases}), 52)
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
        }.issubset(ids))

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
        self.assertIn("expert mode", skill)
        self.assertIn("guided mode", skill)
        self.assertIn("scripts/run_demo.py", skill)
        self.assertIn("never let `demo works` imply `ready for production`", skill)

    def test_manifest_identity_and_versions_match(self):
        codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(codex["name"], claude["name"])
        self.assertEqual(codex["version"], claude["version"])
        self.assertEqual(codex["name"], "lago-billing")


if __name__ == "__main__":
    unittest.main()
