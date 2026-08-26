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

    def test_reconciliation_passes(self):
        result = run("reconcile.py", FIXTURES / "reconcile-source.csv", FIXTURES / "reconcile-lago-pass.csv")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_reconciliation_classifies_differences(self):
        result = run("reconcile.py", FIXTURES / "reconcile-source.csv", FIXTURES / "reconcile-lago-diff.csv")
        self.assertEqual(result.returncode, 2)
        classes = {item["class"] for item in json.loads(result.stdout)["discrepancies"]}
        self.assertEqual(classes, {"amount mismatch", "missing in Lago", "missing in source"})

    def test_eval_suite_has_all_44_unique_cases(self):
        data = json.loads((ROOT / "evals/implementation/cases.json").read_text(encoding="utf-8"))
        cases = data["cases"]
        self.assertEqual(len(cases), 44)
        self.assertEqual(len({case["id"] for case in cases}), 44)
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

    def test_manifest_identity_and_versions_match(self):
        codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(codex["name"], claude["name"])
        self.assertEqual(codex["version"], claude["version"])
        self.assertEqual(codex["name"], "lago-billing")


if __name__ == "__main__":
    unittest.main()
