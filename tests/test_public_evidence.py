"""Archived evidence in this public repository carries results, not private context."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = [*ROOT.glob("docs/release-evidence/**/*"), *ROOT.glob("evals/*/evidence/**/*")]
SPEND_KEYS = {"costUsd", "judgeCostUsd", "cost_usd", "total_cost_usd"}
# File listings expose the local account name; redacted transcripts show <user>.
LISTING_OWNER = re.compile(r"[d-][rwx-]{9}[@+.]?\s+\d+\s+(?!<user>)[A-Za-z0-9_.-]+\s+\S+\s+\d+")
LOCAL_PATH = re.compile(r"/(?:Users|home|opt/homebrew|private/var|var/folders)/")
ROLE_LABEL = re.compile(r"\bCTO\b")


def keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from keys(item)


class PublicEvidenceTests(unittest.TestCase):
    def test_evidence_files_exist(self):
        self.assertTrue([p for p in EVIDENCE if p.is_file()])

    def test_no_spend_thinking_or_local_context(self):
        for path in (p for p in EVIDENCE if p.is_file() and p.suffix in (".json", ".md")):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertIsNone(LISTING_OWNER.search(text), "unredacted file owner in a directory listing")
                self.assertIsNone(LOCAL_PATH.search(text), "local machine path")
                self.assertIsNone(ROLE_LABEL.search(text), "internal role label")
                if path.suffix == ".json":
                    found = list(keys(json.loads(text)))
                    self.assertFalse(SPEND_KEYS & {k for k, _ in found}, "spend field")
                    thinking = [v for k, v in found if k == "thinking" and v != "[omitted]"]
                    self.assertFalse(thinking, "model thinking content")
                    self.assertNotIn("signature", {k for k, v in found if isinstance(v, str) and len(v) > 200})


if __name__ == "__main__":
    unittest.main()
