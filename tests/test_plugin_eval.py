"""Eval suites run against a staged copy of the shipped plugin, never the repository root."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load():
    spec = importlib.util.spec_from_file_location("plugin_eval", ROOT / "scripts/plugin_eval.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PluginEvalTests(unittest.TestCase):
    def setUp(self):
        self.runner = load()

    def test_staged_plugin_holds_suite(self):
        with self.runner.staged("evals/safety") as plugin:
            self.assertTrue((plugin / ".claude-plugin/plugin.json").is_file())
            self.assertTrue((plugin / "evals/safety/planted-repo-instructions/case.yaml").is_file())
            self.assertFalse((plugin / "RELEASE-MANIFEST.json").exists())
            self.assertFalse((ROOT / "plugins/lago/evals").exists())
        self.assertFalse(plugin.exists())

    def test_rejects_paths_outside_evals(self):
        for suite in ("tests", "plugins/lago/skills", "evals/does-not-exist"):
            with self.subTest(suite=suite), self.assertRaises(ValueError):
                with self.runner.staged(suite):
                    pass


if __name__ == "__main__":
    unittest.main()
