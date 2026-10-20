#!/usr/bin/env python3
"""Run a repository eval suite against the shipped plugin with `claude plugin eval`.

`claude plugin eval` reads cases only from inside the plugin folder, and the eval
suites stay outside `plugins/lago/` so they never ship. This stages a temporary
copy of the plugin with one suite at the same relative path, regenerates the staged
copy's RELEASE-MANIFEST.json so the skill's integrity check sees a consistent
bundle (as it did when the suites lived inside the plugin), runs the eval there,
and removes the copy. Standard library only.

Usage: plugin_eval.py SUITE [claude plugin eval options...]
  e.g. plugin_eval.py evals/safety --ablation none --threshold 1 --scaffold \\
           --allow-tools Bash Write Edit WebFetch --trust-plugin --no-publish

Without --output-dir, results go to SUITE/results/<timestamp>/, which is gitignored.
"""

from __future__ import annotations

import contextlib
import importlib.util
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PLUGIN = REPO / "plugins/lago"
IGNORED = shutil.ignore_patterns("__pycache__", "results", ".DS_Store")


def integrity_module():
    spec = importlib.util.spec_from_file_location(
        "release_integrity", PLUGIN / "skills/implementation/scripts/release_integrity.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def staged(suite: str):
    """Yield a temporary plugin folder that holds `suite` at the same relative path."""
    source = (REPO / suite).resolve()
    relative = source.relative_to(REPO)
    if relative.parts[0] != "evals" or not source.is_dir():
        raise ValueError(f"suite must be a directory under evals/: {suite}")
    with tempfile.TemporaryDirectory(prefix="lago-plugin-eval-") as directory:
        plugin = Path(directory) / "lago"
        shutil.copytree(PLUGIN, plugin, ignore=IGNORED)
        shutil.copytree(source, plugin / relative, ignore=IGNORED)
        integrity_module().create(plugin, plugin / "RELEASE-MANIFEST.json")
        yield plugin


def main(argv: list[str]) -> int:
    if not argv or argv[0].startswith("-"):
        print(__doc__, file=sys.stderr)
        return 2
    suite, options = argv[0].rstrip("/"), argv[1:]
    if "--output-dir" not in options:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        options += ["--output-dir", str(REPO / suite / "results" / stamp)]
    with staged(suite) as plugin:
        command = ["claude", "plugin", "eval", str(plugin), "--eval-dir", suite, *options]
        return subprocess.run(command, cwd=REPO).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
