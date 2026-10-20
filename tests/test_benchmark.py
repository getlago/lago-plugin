"""The benchmark scorer passes correct billing code and fails each targeted defect."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "evals/benchmark"
SCAFFOLD = BENCH / "tasks/python-usage-billing/scaffold.sh"
REFERENCE = (BENCH / "reference/billing.py").read_text(encoding="utf-8")


def load_score():
    spec = importlib.util.spec_from_file_location("bench_score", BENCH / "checks/score.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["bench_score"] = module
    spec.loader.exec_module(module)
    return module


def mutate(old: str, new: str) -> str:
    assert old in REFERENCE, old
    return REFERENCE.replace(old, new)


# Each mutation is a realistic billing bug and the one criterion that must catch it.
MUTANTS = {
    "transaction id minted per attempt": (
        mutate('event = {"transaction_id": row["transaction_id"],', 'event = {"transaction_id": __import__("uuid").uuid4().hex,'),
        "idempotent_events"),
    "timestamp taken at send time": (
        mutate('"timestamp": f"{row[\'occurred_at\']:.3f}"', '"timestamp": f"{__import__(\'time\').time():.3f}"'),
        "idempotent_events"),
    "replay creates a new event": (
        mutate('(generation_id, f"gen_{generation_id}",', '(generation_id + __import__("uuid").uuid4().hex, f"gen_{generation_id}_{__import__(\'uuid\').uuid4().hex}",'),
        "no_double_billing"),
    "subscription reuses the customer id": (
        mutate('return f"sub_{workspace_id}"', "return workspace_id"),
        "no_double_billing"),
    "price per token instead of per thousand": (
        mutate('"properties": {"amount": "0.00002"}', '"properties": {"amount": "0.02"}'),
        "correct_charges"),
    "webhook signature not checked": (
        mutate('    if not hmac.compare_digest(expected, headers.get("X-Lago-Signature") or ""):\n        return 401\n', ""),
        "webhook_verification"),
}


class BenchmarkPrivacyTests(unittest.TestCase):
    def test_no_benchmark_results_in_repository(self):
        # Results are private by design: the runner writes outside the repository only.
        tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
        names = {"report.json", "eval-result.json", "eval.log", "aggregate-result.json"}
        leaked = [p for p in tracked if p.startswith("evals/benchmark/")
                  and (Path(p).name in names or "/results/" in p or "/workspaces/" in p)]
        self.assertEqual(leaked, [])

    def test_runner_refuses_output_inside_repository(self):
        result = subprocess.run([sys.executable, str(BENCH / "run_benchmark.py"), "--out", str(BENCH / "results")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("--out must be outside the repository", result.stderr)

    def test_runner_never_publishes_reports(self):
        self.assertIn('"--no-publish"', (BENCH / "run_benchmark.py").read_text(encoding="utf-8"))


@unittest.skipUnless(shutil.which("bash"), "bash is required for the task scaffold")
class BenchmarkScorerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.score = load_score()

    def run_solution(self, source: str) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            subprocess.run(["bash", str(SCAFFOLD)], cwd=workspace, check=True, capture_output=True)
            (workspace / "billing.py").write_text(source, encoding="utf-8")
            result = self.score.score(workspace, timeout=60)
        self.assertEqual(result["status"], "scored", result)
        return {name: value["result"] for name, value in result["criteria"].items()}

    def test_reference_passes_every_criterion(self):
        self.assertEqual(set(self.run_solution(REFERENCE).values()), {"pass"})

    def test_each_defect_fails_its_criterion(self):
        for name, (source, criterion) in MUTANTS.items():
            with self.subTest(defect=name):
                results = self.run_solution(source)
                # Only the targeted criterion fails, so a crash cannot pass for detection.
                self.assertEqual([k for k, v in results.items() if v == "fail"], [criterion], results)

    def test_broken_module_fails_everything_without_crashing_the_scorer(self):
        results = self.run_solution("raise RuntimeError('not implemented')\n")
        self.assertEqual(set(results.values()), {"fail"})


if __name__ == "__main__":
    unittest.main()
