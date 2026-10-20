"""Every agent entry point shows the same install commands as the README."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = re.compile(r"^(?:/plugin|codex plugin) [^\n`]+$", re.M)
ENTRY_POINTS = ("START_HERE.md", "llms.txt")


class InstallCommandTests(unittest.TestCase):
    def test_readme_install_identity(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        install = readme.split("## Install", 1)[1].split("## Start here", 1)[0]
        self.assertEqual(INSTALL.findall(install), [
            "/plugin marketplace add getlago/lago-plugin",
            "/plugin install lago@lago-plugins",
            "codex plugin marketplace add getlago/lago-plugin",
            "codex plugin add lago@lago-plugins",
        ])

    def assert_install_flow(self, text):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        commands = INSTALL.findall(readme.split("## Install", 1)[1].split("## Start here", 1)[0])
        for add, install, invocation in (
            (commands[0], commands[1], "/lago:implementation"),
            (commands[2], commands[3], "$lago:implementation"),
        ):
            for command in (add, install, invocation):
                self.assertIn(command, text)
            self.assertLess(text.index(add), text.index(install))
            self.assertLess(text.index(install), text.index(invocation))
        self.assertRegex(text.lower(), r"new (?:codex )?task")

    def test_entry_points_match_readme(self):
        for entry in ENTRY_POINTS:
            with self.subTest(entry=entry):
                self.assert_install_flow((ROOT / entry).read_text(encoding="utf-8"))

    @unittest.skipUnless(shutil.which("node"), "node is required to inspect init output")
    def test_init_prints_complete_install_flow_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory)
            manifest = app / "package.json"
            manifest.write_text('{"dependencies":{"next":"15.0.0"}}', encoding="utf-8")
            result = subprocess.run(
                ["node", str(ROOT / "packages/init/bin/lago-init.js"), str(app)],
                capture_output=True, text=True, check=True, timeout=15,
            )
            self.assert_install_flow(result.stdout)
            self.assertIn("interactive Claude Code session", result.stdout)
            self.assertIn("in your terminal", result.stdout)
            self.assertEqual(list(app.iterdir()), [manifest], "dry run must not write files")


if __name__ == "__main__":
    unittest.main()
