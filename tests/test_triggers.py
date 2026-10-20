"""Structure checks for the trigger eval suite and local eval output handling."""

from __future__ import annotations

import importlib.util
import re
import sys
import unittest
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

    def test_summary_counts_turn_capped_runs(self):
        summarize = load("trigger_summarize", TRIGGERS / "summarize.py")
        result = {"claudeVersion": "test", "costUsd": 1, "cases": [
            {"name": "seat-plus-usage", "arms": {"with": [
                {"error": "exit 1: Reached maximum number of turns (4)", "graders": [{"passed": True}]},
                {"error": None, "graders": [{"passed": False}]},
                {"error": "timed out", "graders": []},
            ]}},
            {"name": "eu-vat-calculation", "arms": {"with": [{"error": None, "graders": [{"passed": False}]}]}},
        ]}
        summary = summarize.summarize(result)
        self.assertEqual(summary["hit_rate"], "1/2")
        self.assertEqual(summary["false_trigger_rate"], "1/1")
        self.assertEqual(summary["false_triggers"], ["eu-vat-calculation"])

    def test_description_fits_agent_skills_limit(self):
        # https://agentskills.io/specification: description is 1-1024 characters.
        frontmatter = (ROOT / "skills/implementation/SKILL.md").read_text(encoding="utf-8").split("\n---\n", 1)[0]
        description = re.search(r"^description: (.+)$", frontmatter, re.M).group(1)
        self.assertLessEqual(len(description), 1024)
        self.assertNotIn(": ", description, "a colon-space breaks the unquoted YAML value")

    def test_eval_output_is_outside_the_bundle_but_nothing_else_is(self):
        integrity = load("release_integrity_under_test", ROOT / "skills/implementation/scripts/release_integrity.py")
        self.assertTrue(integrity.is_eval_output(Path("evals/triggers/results/run/aggregate-result.json")))
        self.assertFalse(integrity.is_eval_output(Path("evals/triggers/positive/seat-plus-usage/prompt.md")))
        self.assertFalse(integrity.is_eval_output(Path("skills/implementation/results/x.json")))
        self.assertFalse(integrity.is_eval_output(Path("evals/results/x.json")))


if __name__ == "__main__":
    unittest.main()
