"""Fresh-agent evidence must identify the source and prove no plugin was loaded."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class FreshAgentRunnerTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("fresh_runner", ROOT / "evals/fresh-agent/run.py")
        self.runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.runner)
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "evidence"
        self.addCleanup(self.tmp.cleanup)

    def run_case(self, error=None, model="verified-model", plugin=False, passed=True):
        def execute(command, **kwargs):
            staged = Path(command[3])
            self.assertFalse((staged / ".claude-plugin").exists())
            self.assertIn("/candidate/START_HERE.md", (staged / "evals/nextjs-start-here/prompt.md").read_text())
            self.assertIn("WebFetch(domain:raw.githubusercontent.com)", command)
            self.assertIn("--no-publish", command)
            self.out.mkdir()
            trace = self.out / "trace.jsonl"
            trace.write_text(json.dumps({"type": "system", "subtype": "init", "model": model,
                                        "plugins": [{"name": "lago"}] if plugin else []}) + "\n")
            result = {"cases": [{"arms": {"with": [{"passed": passed, "error": error,
                       "tracePath": str(trace), "graders": [{"name": "billing", "passed": passed}]}]}}]}
            (self.out / "aggregate-result.json").write_text(json.dumps(result))
            return subprocess.CompletedProcess(command, 0)
        def git(*args):
            return "" if args[0] == "status" else "candidate"
        with patch("sys.argv", ["run.py", "--out", str(self.out), "--model", "requested-model", "--runs", "1"]), \
             patch.object(self.runner, "git", side_effect=git), \
             patch.object(self.runner.subprocess, "run", side_effect=execute), \
             patch.object(self.runner.subprocess, "check_output", return_value="claude-test"):
            status = self.runner.main()
        return status, json.loads((self.out / "summary.json").read_text())

    def test_pins_source_and_records_observed_model(self):
        status, result = self.run_case()
        self.assertEqual(status, 0)
        self.assertTrue(result["complete"])
        self.assertEqual(result["source_commit"], "candidate")
        self.assertEqual(result["runs"][0]["models"], ["verified-model"])

    def test_incomplete_and_contaminated_runs_never_pass(self):
        for inputs in ({"error": "timeout"}, {"model": None}, {"plugin": True}):
            with self.subTest(inputs=inputs):
                # Each invocation requires a new evidence directory.
                self.out = Path(self.tmp.name) / str(len(list(Path(self.tmp.name).iterdir())))
                status, result = self.run_case(**inputs)
                self.assertEqual(status, 1)
                self.assertFalse(result["complete"])

    def test_failed_billing_check_exits_nonzero(self):
        status, result = self.run_case(passed=False)
        self.assertEqual(status, 1)
        self.assertTrue(result["complete"])
        self.assertFalse(result["runs"][0]["passed"])

    def test_refuses_outputs_inside_repository(self):
        with patch("sys.argv", ["run.py", "--out", str(ROOT / "private-evidence"), "--model", "test"]):
            with self.assertRaises(SystemExit) as raised:
                self.runner.main()
            self.assertEqual(raised.exception.code, 2)
