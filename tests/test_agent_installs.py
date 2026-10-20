"""Failure cases for install evidence and the Gemini installation record."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InstallVerificationTests(unittest.TestCase):
    def setUp(self):
        self.runner = load("verify_installs", ROOT / "evals/agent-installs/verify_installs.py")
        self.integrity = load("release_integrity", ROOT / "skills/implementation/scripts/release_integrity.py")

    def test_gemini_metadata_exception_keeps_code_and_extra_files_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "gemini-extension.json").write_text('{"name":"lago","version":"test"}')
            code = root / "demo.py"
            code.write_text("original")
            manifest = root / "RELEASE-MANIFEST.json"
            self.integrity.create(root, manifest)
            metadata = root / ".gemini-extension-install.json"
            metadata.write_text('{"type":"local","source":"synthetic"}')
            result = self.integrity.check(root, manifest)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["install_metadata"], [metadata.name])
            code.write_text("changed")
            self.assertEqual(self.integrity.check(root, manifest)["changed"], ["demo.py"])
            code.write_text("original")
            extra = root / "unexpected.py"
            extra.write_text("unexpected")
            self.assertEqual(self.integrity.check(root, manifest)["unexpected"], [extra.name])
            extra.unlink()
            nested = root / "nested"
            nested.mkdir()
            (nested / metadata.name).write_text("{}")
            self.assertEqual(self.integrity.check(root, manifest)["unexpected"], ["nested/" + metadata.name])
            metadata.unlink()
            metadata.symlink_to(code)
            with self.assertRaises(self.integrity.IntegrityError):
                self.integrity.check(root, manifest)

    def test_metadata_is_not_exempt_without_gemini_or_when_manifested(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "code.py").write_text("synthetic")
            manifest = root / "RELEASE-MANIFEST.json"
            self.integrity.create(root, manifest)
            metadata = root / ".gemini-extension-install.json"
            metadata.write_text("{}")
            self.assertEqual(self.integrity.check(root, manifest)["unexpected"], [metadata.name])
            (root / "gemini-extension.json").write_text("{}")
            self.integrity.create(root, manifest)
            metadata.write_text('{"changed":true}')
            self.assertEqual(self.integrity.check(root, manifest)["changed"], [metadata.name])

    def test_gemini_install_success_is_not_enough_without_integrity(self):
        step = {"exit_code": 0, "output_tail": ["successfully validated", "implementation [Enabled]"]}
        with tempfile.TemporaryDirectory() as directory, patch.object(self.runner, "run", return_value=step), patch.object(self.runner, "installed_skill", return_value={"identical": 1}), patch.object(self.runner, "verify_bundle", return_value={"status": "FAIL"}):
            result = self.runner.check_gemini(Path(directory))
        self.assertFalse(result["passed"])
        self.assertFalse(result["offline_demo"]["passed"])

    def test_copilot_rejects_wrong_live_source_despite_success_output(self):
        step = {"exit_code": 0, "output_tail": ["Installed 1 skill", "lago@lago-plugins enabled"]}
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            (home / ".copilot").mkdir()
            settings = {"enabledPlugins": {"lago@lago-plugins": True}, "extraKnownMarketplaces": {
                "lago-plugins": {"source": {"source": "directory", "path": str(home / "wrong")}}}}
            (home / ".copilot/settings.json").write_text(json.dumps(settings))
            with patch.object(self.runner, "run", return_value=step), patch.object(self.runner, "verify_bundle", return_value={"status": "PASS"}), patch.object(self.runner, "verify_demo", return_value={"passed": True}):
                result = self.runner.check_copilot(home)
            self.assertFalse(result["passed"])
            self.assertFalse(result["source_matches_checkout"])

    def test_sanitize_commands_and_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            value = f"timeout: {home.resolve()}/file {self.runner.REPO}/file"
            self.assertEqual(self.runner.sanitize(value, home), "timeout: <home>/file <checkout>/file")

    def test_failed_integrity_never_executes_installed_demo(self):
        with patch.object(self.runner, "run") as run:
            result = self.runner.verify_demo(Path("synthetic"), Path("synthetic"), {"status": "FAIL"})
        self.assertFalse(result["passed"])
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
