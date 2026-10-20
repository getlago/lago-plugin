"""Structure checks for the automated safety eval suite."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAFETY = ROOT / "evals/safety"
SYNTHETIC_KEY = "8d1c7a52-3f0e-4c9b-9a61-2b7e5d4f0c13"
SINGLE_QUOTED = re.compile(r"^[a-z_]+: '(.*)'$", re.M)


class SafetyEvalTests(unittest.TestCase):
    def cases(self):
        return sorted(p for p in SAFETY.iterdir() if p.is_dir())

    def test_cases_cover_the_release_safety_gates(self):
        self.assertEqual({c.name for c in self.cases()}, {
            "planted-repo-instructions", "pasted-production-key-chat", "unsafe-production-write",
            "dry-run-approval-laundering", "cloud-staging-demo-refusal", "production-credentials",
            "credential-presence-preflight", "remote-self-hosted-demo-target", "tampered-plugin-bundle",
        })

    def test_each_case_has_scaffold_prompt_judge_and_a_deterministic_grader(self):
        for case in self.cases():
            with self.subTest(case=case.name):
                self.assertIn("scaffold_script: scaffold.sh", (case / "case.yaml").read_text(encoding="utf-8"))
                self.assertTrue((case / "scaffold.sh").stat().st_mode & 0o111)
                graders = {g.name: g.read_text(encoding="utf-8") for g in (case / "graders").glob("*.md")}
                self.assertIn("type: llm", graders.pop("gate-held.md"))
                self.assertTrue(any("type: tool_used" in g or "type: regex" in g for g in graders.values()))

    def test_single_quoted_yaml_values_escape_quotes(self):
        # In YAML single-quoted scalars, a literal quote must be written as ''.
        for grader in SAFETY.glob("*/graders/*.md"):
            for value in SINGLE_QUOTED.findall(grader.read_text(encoding="utf-8")):
                with self.subTest(grader=str(grader.relative_to(ROOT))):
                    self.assertNotRegex(value.replace("''", ""), "'")

    def test_credentials_are_synthetic(self):
        # The only key-shaped value in the suite is the documented synthetic UUID.
        for path in SAFETY.rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                keys = set(re.findall(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", text))
                self.assertLessEqual(keys, {SYNTHETIC_KEY}, str(path))


if __name__ == "__main__":
    unittest.main()
