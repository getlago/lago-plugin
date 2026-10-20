"""Per-agent manifests are generated from .claude-plugin/ and never drift."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/implementation/scripts"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AgentFileTests(unittest.TestCase):
    def test_committed_files_match_generator(self):
        result = subprocess.run([sys.executable, str(SCRIPTS / "build_agent_files.py"), str(ROOT), "--check"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_manifests_carry_the_shared_identity(self):
        claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        gemini = json.loads((ROOT / "gemini-extension.json").read_text(encoding="utf-8"))
        cursor = json.loads((ROOT / ".cursor-plugin/plugin.json").read_text(encoding="utf-8"))
        market = json.loads((ROOT / ".cursor-plugin/marketplace.json").read_text(encoding="utf-8"))
        for manifest in (gemini, cursor):
            self.assertEqual((manifest["name"], manifest["version"]), (claude["name"], claude["version"]))
        # Gemini requires name and version; the name is lowercase with dashes.
        self.assertRegex(gemini["name"], r"^[a-z0-9-]+$")
        self.assertEqual(cursor["skills"], "./skills/")
        self.assertEqual(market["name"], "lago-plugins")
        self.assertRegex(market["name"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        self.assertEqual(market["owner"]["name"], "Lago")
        self.assertEqual([(p["name"], p["source"]) for p in market["plugins"]], [("lago", "./")])

    def test_check_detects_drift_and_root_manifest(self):
        validate = load("validate_repo")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "copy"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__", "results"))
            gemini = root / "gemini-extension.json"
            gemini.write_text(gemini.read_text(encoding="utf-8").replace('"0.2.0"', '"9.9.9"'), encoding="utf-8")
            (root / "plugin.json").write_text("{}", encoding="utf-8")
            failures = validate.validate(root, None)
            self.assertIn("generated agent manifest is stale: gemini-extension.json (run build_agent_files.py)", failures)
            self.assertTrue(any(f.startswith("root plugin.json would take precedence") for f in failures))

    def test_skill_frontmatter_uses_only_spec_fields(self):
        # skills-ref rejects keys outside this set; agents that copy only the skill rely on it.
        frontmatter = (ROOT / "skills/implementation/SKILL.md").read_text(encoding="utf-8").split("\n---\n", 1)[0]
        keys = set(re.findall(r"^([a-z-]+):", frontmatter, re.M))
        self.assertLessEqual(keys, {"name", "description", "license", "allowed-tools", "metadata", "compatibility"})
        self.assertIn("name: implementation", frontmatter)


if __name__ == "__main__":
    unittest.main()
