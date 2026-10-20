"""Every agent entry point shows the same install commands as the README."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = re.compile(r"^(?:/plugin|codex plugin) [^\n`]+$", re.M)
ENTRY_POINTS = ("START_HERE.md", "llms.txt", "packages/init/bin/lago-init.js")


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

    def test_entry_points_match_readme(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        commands = INSTALL.findall(readme.split("## Install", 1)[1].split("## Start here", 1)[0])
        for entry in ENTRY_POINTS:
            text = (ROOT / entry).read_text(encoding="utf-8")
            for command in commands:
                with self.subTest(entry=entry, command=command):
                    self.assertIn(command, text)
            if entry != "packages/init/bin/lago-init.js":
                with self.subTest(entry=entry, invocation=True):
                    self.assertIn("/lago:implementation", text)
                    self.assertIn("$lago:implementation", text)


if __name__ == "__main__":
    unittest.main()
