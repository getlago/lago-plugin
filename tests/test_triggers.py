"""Structure checks for the trigger eval suite and local eval output handling."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import re
import sys
import unittest
from unittest.mock import Mock, patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRIGGERS = ROOT / "evals/triggers"
SKILL_GRADER = re.compile(r"input_match: '\"skill\"\\s\*:\\s\*\"\(\?:\[\\w-\]\+:\)\?implementation\"'")


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TriggerSuiteTests(unittest.TestCase):
    def cases(self, kind: str) -> list[Path]:
        return sorted(path for path in (TRIGGERS / kind).iterdir() if path.is_dir())

    def test_suite_size_and_balance(self):
        self.assertGreaterEqual(len(self.cases("positive")), 30)
        self.assertGreaterEqual(len(self.cases("negative")), 15)

    def test_every_case_has_one_skill_grader(self):
        for kind, grader, bounds in (("positive", "fired.md", ""), ("negative", "not-fired.md", "min: 0\nmax: 0\n")):
            for case in self.cases(kind):
                with self.subTest(case=case.name):
                    prompt = (case / "prompt.md").read_text(encoding="utf-8")
                    self.assertIn(f"tags: [trigger, {kind}]", prompt)
                    self.assertIn("allowed_tools: [Read, Glob, Grep, Skill]", prompt)
                    text = (case / "graders" / grader).read_text(encoding="utf-8")
                    self.assertIn("type: tool_used\ntool: Skill\n", text)
                    self.assertRegex(text, SKILL_GRADER)
                    self.assertIn(bounds, text)

    def test_positive_prompts_mostly_avoid_naming_lago(self):
        named = [c.name for c in self.cases("positive") if "lago" in (c / "prompt.md").read_text(encoding="utf-8").lower()]
        self.assertLessEqual(len(named), 2, named)

    def test_summary_rejects_turn_capped_runs(self):
        summarize = load("trigger_summarize", TRIGGERS / "summarize.py")
        result = {"claudeVersion": "test", "costUsd": 1, "cases": [
            {"name": "seat-plus-usage", "runsPerCase": 3, "arms": {"with": [
                {"error": "exit 1: Reached maximum number of turns (4)", "graders": [{"name": "fired", "passed": True}]},
                {"error": None, "graders": [{"name": "fired", "passed": False}]},
                {"error": "timed out", "graders": []},
            ]}},
            {"name": "eu-vat-calculation", "runsPerCase": 1, "arms": {"with": [{"error": None, "graders": [{"name": "not-fired", "passed": False}]}]}},
        ]}
        summary = summarize.summarize(result)
        self.assertFalse(summary["complete"])
        self.assertEqual(summary["coverage"]["positive"]["errors"], 2)
        self.assertEqual(summary["coverage"]["positive"]["planned"], 3)
        self.assertEqual(summary["hit_rate"], "0/1")
        self.assertEqual(summary["false_trigger_rate"], "1/1")
        self.assertEqual(summary["false_triggers"], ["eu-vat-calculation"])

    def test_codex_requires_successful_exact_read(self):
        runner = load("codex_triggers", TRIGGERS / "codex_triggers.py")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "SKILL.md"
            path.write_text("Synthetic skill contents\n")
            event = {"type": "item.completed", "item": {
                "type": "command_execution", "status": "completed", "exit_code": 0,
                "command": f"cat {path}", "aggregated_output": path.read_text()}}
            self.assertTrue(runner.observed_read(event, path))
            # Shell startup diagnostics share aggregated_output with a successful cat.
            noisy = {**event, "item": {**event["item"], "aggregated_output":
                "shell startup: process listing denied\n" + path.read_text() + "shell warning\n"}}
            self.assertTrue(runner.observed_read(noisy, path))
            for field, value in [("command", "echo implementation/SKILL.md"),
                                 ("command", "cat /unrelated/implementation/SKILL.md"),
                                 ("command", f"echo cat {path}"),
                                 ("command", f"cat {path}; true"),
                                 ("exit_code", 1), ("status", "failed"),
                                 ("aggregated_output", "No such file"),
                                 ("aggregated_output", "Synthetic"),
                                 ("aggregated_output", "Synthetic skill contents altered")]:
                with self.subTest(field=field, value=value):
                    changed = {**event, "item": {**event["item"], field: value}}
                    self.assertFalse(runner.observed_read(changed, path))
            self.assertFalse(runner.observed_read({**event, "type": "item.started"}, path))

    def test_codex_reaps_process_after_verified_read(self):
        runner = load("codex_triggers", TRIGGERS / "codex_triggers.py")
        process = Mock()
        process.stdout = Mock(wraps=None)
        process.stdout.__iter__ = Mock(return_value=iter(['{"type":"item.completed","item":{"command":"cat skill", "exit_code":0}}\n']))
        process.poll.return_value = None
        with patch.object(runner.subprocess, "run"), patch.object(runner.subprocess, "Popen", return_value=process), patch.object(runner, "observed_read", return_value=True):
            result = runner.run_once("synthetic", 30, None, None)
        self.assertEqual(result["outcome"], "loaded")
        process.kill.assert_called_once()
        process.wait.assert_called_once()
        process.stdout.close.assert_called_once()

    def test_codex_cli_fails_on_incomplete_attempt(self):
        runner = load("codex_triggers", TRIGGERS / "codex_triggers.py")
        with patch.object(sys, "argv", ["codex_triggers.py", "--project-skill"]), patch.object(runner, "load_cases", return_value=[("positive", "synthetic", "prompt")]), patch.object(runner, "run_once", return_value={"outcome": "error", "reason": "timeout"}), patch.object(runner.subprocess, "check_output", return_value="test"), patch("builtins.print"):
            self.assertEqual(runner.main(), 1)

    def test_codex_rejects_changed_or_dirty_source(self):
        runner = load("codex_triggers", TRIGGERS / "codex_triggers.py")
        for dirty, changed in ((False, False), (True, False), (False, True)):
            before = {"source_commit": "before", "source_dirty": dirty}
            after = {**before, "source_commit": "after"} if changed else before
            with self.subTest(dirty=dirty, changed=changed), patch.object(sys, "argv", ["runner", "--project-skill"]), patch.object(runner, "load_cases", return_value=[("positive", "synthetic", "prompt")]), patch.object(runner, "run_once", return_value={"outcome": "loaded"}), patch.object(runner, "source_metadata", side_effect=[before, after]), patch.object(runner.subprocess, "check_output", return_value="test"), patch("builtins.print") as output:
                self.assertEqual(runner.main(), int(dirty or changed))
                result = json.loads(output.call_args.args[0])
                self.assertEqual(result["source_commit"], "before")
                self.assertEqual(result["source_changed"], changed)

    def test_codex_coverage_preserves_each_error(self):
        runner = load("codex_triggers", TRIGGERS / "codex_triggers.py")
        runs = [{"kind": "positive", "outcome": outcome} for outcome in ("loaded", "error", "error")]
        summary = runner.summarize_runs(runs)
        self.assertFalse(summary["complete"])
        self.assertEqual(summary["coverage"]["positive"], {"planned": 3, "completed": 1, "errors": 2, "loaded": 1})
        self.assertEqual(len(summary["runs"]), 3)
        self.assertFalse(runner.summarize_runs([])["complete"])

    def test_claude_rejects_infrastructure_failure_and_missing_attempts(self):
        summarizer = load("trigger_summarize", TRIGGERS / "summarize.py")
        source = {"cases": [{"name": "eu-vat-calculation", "runsPerCase": 2, "arms": {"with": [
            {"error": "authentication failed", "graders": [{"name": "not-fired", "passed": True}]}
        ]}}]}
        result = summarizer.summarize(source)
        self.assertFalse(result["complete"])
        self.assertEqual(result["false_trigger_rate"], "0/0")
        self.assertEqual(result["coverage"]["negative"]["errors"], 2)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            path.write_text(json.dumps(source))
            process = subprocess.run([sys.executable, str(TRIGGERS / "summarize.py"), str(path)], capture_output=True)
            self.assertEqual(process.returncode, 1)

    def test_claude_requires_expected_grader_and_rejects_partial(self):
        summarizer = load("trigger_summarize", TRIGGERS / "summarize.py")
        source = {"cases": [{"name": "seat-plus-usage", "runsPerCase": 1, "arms": {"with": [
            {"graders": [{"name": "unrelated", "passed": True}]}
        ]}}]}
        self.assertFalse(summarizer.summarize(source)["complete"])
        source["cases"][0]["arms"]["with"][0]["graders"][0]["name"] = "fired"
        self.assertTrue(summarizer.summarize(source)["complete"])
        source["partial"] = True
        self.assertFalse(summarizer.summarize(source)["complete"])

    def test_archived_claude_timeouts_are_not_successful_negatives(self):
        summarizer = load("trigger_summarize", TRIGGERS / "summarize.py")
        for arm, hits, negatives, errors in (("before", "66/76", "2/42", 3), ("after", "71/72", "0/43", 2)):
            with self.subTest(arm=arm):
                result = summarizer.summarize(json.loads((TRIGGERS / "evidence" / f"claude-{arm}.json").read_text()))
                self.assertFalse(result["complete"])
                self.assertEqual(result["hit_rate"], hits)
                self.assertEqual(result["false_trigger_rate"], negatives)
                self.assertEqual(result["coverage"]["negative"]["errors"], errors)

    def test_description_fits_agent_skills_limit(self):
        # https://agentskills.io/specification: description is 1-1024 characters.
        frontmatter = (ROOT / "plugins/lago/skills/implementation/SKILL.md").read_text(encoding="utf-8").split("\n---\n", 1)[0]
        description = re.search(r"^description: (.+)$", frontmatter, re.M).group(1)
        self.assertLessEqual(len(description), 1024)
        self.assertNotIn(": ", description, "a colon-space breaks the unquoted YAML value")

    def test_eval_output_is_outside_the_bundle_but_nothing_else_is(self):
        integrity = load("release_integrity_under_test", ROOT / "tools/release/release_integrity.py")
        self.assertTrue(integrity.is_eval_output(Path("evals/triggers/results/run/aggregate-result.json")))
        self.assertFalse(integrity.is_eval_output(Path("evals/triggers/positive/seat-plus-usage/prompt.md")))
        self.assertFalse(integrity.is_eval_output(Path("skills/implementation/results/x.json")))
        self.assertFalse(integrity.is_eval_output(Path("evals/results/x.json")))


if __name__ == "__main__":
    unittest.main()
