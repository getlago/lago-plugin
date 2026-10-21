"""The plugin directory file limits fail closed on each documented violation."""
from __future__ import annotations

import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load():
    spec = importlib.util.spec_from_file_location("check_directory_limits", ROOT / "scripts/check_directory_limits.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(repo: Path, *args: str) -> None:
    env = {**os.environ, "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.com",
           "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.com"}
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, env=env)


class DirectoryLimitTests(unittest.TestCase):
    def setUp(self):
        self.limits = load()
        self.directory = tempfile.TemporaryDirectory()
        self.repo = Path(self.directory.name)
        self.plugin = self.repo / "plugins/lago"
        (self.plugin / ".claude-plugin").mkdir(parents=True)
        (self.plugin / ".claude-plugin/plugin.json").write_text('{"name": "lago"}\n')
        (self.plugin / "README.md").write_text("A readme.\n")
        git(self.repo, "init", "-q")

    def tearDown(self):
        self.directory.cleanup()

    def failures(self) -> list[str]:
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "fixture", "--allow-empty")
        failures, _ = self.limits.check(self.repo, self.plugin)
        return failures

    def test_clean_plugin_passes(self):
        self.assertEqual(self.failures(), [])

    def test_repository_plugin_passes(self):
        failures, counts = self.limits.check(ROOT, ROOT / "plugins/lago")
        self.assertEqual(failures, [])
        self.assertLessEqual(counts["plugin_files"], self.limits.MAX_PLUGIN_FILES)

    def test_junk_files_fail(self):
        for name in (".DS_Store", "Thumbs.db", "desktop.ini"):
            (self.plugin / name).write_bytes(b"x")
        failures = self.failures()
        for name in (".DS_Store", "Thumbs.db", "desktop.ini"):
            self.assertIn(f"operating-system junk file: plugins/lago/{name}", failures)

    def test_large_text_file_fails_but_large_image_passes(self):
        (self.plugin / "big.md").write_text("a" * (self.limits.MAX_TEXT_BYTES + 1))
        (self.plugin / "icon.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x01" * (self.limits.MAX_TEXT_BYTES + 1))
        failures = self.failures()
        self.assertTrue(any(f.endswith(": plugins/lago/big.md") for f in failures))
        self.assertFalse(any("icon.png" in f for f in failures))

    def test_disallowed_binary_fails(self):
        (self.plugin / "bundle.zip").write_bytes(b"PK\x03\x04\x00\x00")
        self.assertIn("binary file other than PNG, JPEG, GIF, WebP, or a font: plugins/lago/bundle.zip", self.failures())

    def test_file_count_limit(self):
        for index in range(self.limits.MAX_PLUGIN_FILES):
            (self.plugin / f"f{index}.md").write_text("x")
        self.assertTrue(any(f.startswith("plugin folder has 514 files") for f in self.failures()))

    def test_symlink_fails(self):
        (self.plugin / "link.md").symlink_to("README.md")
        self.assertIn("symbolic link: plugins/lago/link.md", self.failures())

    def test_case_collision_fails(self):
        (self.plugin / "notes.md").write_text("a")
        git(self.repo, "add", "-A")
        # A case-insensitive file system cannot hold both names, so stage the second one directly.
        blob = subprocess.run(["git", "-C", str(self.repo), "hash-object", "-w", "--stdin"], input=b"b",
                              capture_output=True, check=True).stdout.decode().strip()
        git(self.repo, "update-index", "--add", "--cacheinfo", f"100644,{blob},plugins/lago/Notes.md")
        git(self.repo, "commit", "-q", "-m", "fixture")
        failures, _ = self.limits.check(self.repo, self.plugin)
        self.assertTrue(any("differ only by capitalization" in f for f in failures))

    def test_case_colliding_parent_directories_fail(self):
        (self.plugin / "rules").mkdir()
        (self.plugin / "rules/first.md").write_text("a")
        git(self.repo, "add", "-A")
        blob = subprocess.run(["git", "-C", str(self.repo), "hash-object", "-w", "--stdin"], input=b"b",
                              capture_output=True, check=True).stdout.decode().strip()
        git(self.repo, "update-index", "--add", "--cacheinfo", f"100644,{blob},plugins/lago/Rules/second.md")
        git(self.repo, "commit", "-q", "-m", "fixture")
        failures, _ = self.limits.check(self.repo, self.plugin)
        self.assertTrue(any("differ only by capitalization" in f for f in failures))

    def test_missing_plugin_fails(self):
        self.failures()
        failures, counts = self.limits.check(self.repo, self.repo / "missing")
        self.assertEqual(counts["plugin_files"], 0)
        self.assertTrue(any("missing tracked plugin manifest" in f for f in failures))

    def test_root_plugin_counts_and_checks_files(self):
        (self.repo / ".claude-plugin").mkdir()
        (self.repo / ".claude-plugin/plugin.json").write_text('{"name":"root"}')
        (self.repo / "oversize.txt").write_text("x" * (self.limits.MAX_TEXT_BYTES + 1))
        self.failures()
        failures, counts = self.limits.check(self.repo, self.repo)
        self.assertEqual(counts["plugin_files"], 4)
        self.assertTrue(any("oversize.txt" in f for f in failures))

    def test_windows_device_name_fails(self):
        (self.plugin / "con.md").write_text("x")
        self.assertIn("name is invalid on Windows: plugins/lago/con.md", self.failures())

    def test_forbidden_gitattributes_fail(self):
        (self.repo / ".gitattributes").write_text("*.md export-ignore\n*.bin filter=lfs diff=lfs\n")
        failures = self.failures()
        self.assertIn(".gitattributes:1 sets export-ignore, which stops directory validation", failures)
        self.assertIn(".gitattributes:2 sets filter, which stops directory validation", failures)

    def test_plugin_path_characters(self):
        odd = self.repo / "plugins/la go"
        odd.mkdir()
        (odd / "README.md").write_text("x")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "fixture")
        failures, _ = self.limits.check(self.repo, odd)
        self.assertTrue(any(f.startswith("plugin path segment") for f in failures))


if __name__ == "__main__":
    unittest.main()
