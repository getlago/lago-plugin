"""Offline checks for the optional live demo; no Docker or network needed."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/implementation/scripts"
LIVE = SCRIPTS / "live_demo.py"


def load():
    spec = importlib.util.spec_from_file_location("live_demo", LIVE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LiveDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.demo = load()

    def test_expected_money_matches_the_canonical_example(self):
        exp = self.demo.expected()
        self.assertEqual(exp["job_amount"], "0.37")
        self.assertEqual(exp["subscription_invoice"]["total"], "99.00")
        self.assertEqual((exp["usage_invoice"]["quantity"], exp["usage_invoice"]["subtotal"],
                          exp["usage_invoice"]["credits"], exp["usage_invoice"]["total"]), ("1001000", "10.17", "10.00", "0.17"))
        self.assertEqual(exp["period_total"], "99.17")

    def test_every_mutating_phase_requires_its_own_approval(self):
        cases = [["up"], ["up", "--approve", "seed"], ["seed", "--project", "lago-plugin-demo-x"],
                 ["finalize", "--project", "lago-plugin-demo-x", "--approve", "seed"],
                 ["teardown", "--project", "lago-plugin-demo-x", "--approve", "finalize"]]
        for args in cases:
            with self.subTest(args=args):
                env = {"PATH": "/usr/bin:/bin", "LAGO_PLUGIN_DEMO_HOME": str(ROOT / ".no-such-demo-home")}
                result = subprocess.run([sys.executable, str(LIVE), *args], capture_output=True, text=True, env=env)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue("Not approved" in result.stderr or "No demo state" in result.stderr, result.stderr)
                self.assertFalse((ROOT / ".no-such-demo-home").exists())

    def test_plan_changes_nothing_and_shows_every_gate(self):
        result = subprocess.run([sys.executable, str(LIVE), "plan"], capture_output=True, text=True, check=True)
        for phase in ("infrastructure", "seed", "finalize", "teardown"):
            self.assertIn(f"Gate: {phase}", result.stdout)
        for field in ("target", "action", "objects", "billing impact", "infrastructure impact", "recovery"):
            self.assertIn(field, result.stdout)

    def test_projects_must_be_demo_projects(self):
        result = subprocess.run([sys.executable, str(LIVE), "teardown", "--project", "lago_dev", "--approve", "teardown"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("must start with lago-plugin-demo-", result.stderr)

    def test_compose_binds_loopback_only_and_pins_the_digest(self):
        state = {"project": "lago-plugin-demo-t", "api_port": 41001, "ui_port": 41002, "api_url": "http://127.0.0.1:41001",
                 "ui_url": "http://127.0.0.1:41002", "email": "a@example.com", "password": "p", "api_key": "k"}
        compose = self.demo.compose_file(state)
        self.assertIn('"127.0.0.1:41001:3000"', compose)
        self.assertIn('"127.0.0.1:41002:80"', compose)
        self.assertNotIn('"41001:3000"', compose.replace('"127.0.0.1:41001:3000"', ""))
        self.assertRegex(self.demo.IMAGE, r"^getlago/lago:v\d+\.\d+\.\d+@sha256:[0-9a-f]{64}$")
        self.assertIn('LAGO_DISABLE_SIGNUP: "true"', compose)

    def test_extractor_accepts_subscription_fees(self):
        source = ROOT / "tests/fixtures/lago-subscription-invoice-payload.json"
        result = subprocess.run([sys.executable, str(SCRIPTS / "extract_actual.py"), str(source)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        actual = json.loads(result.stdout)
        self.assertEqual((Decimal(actual["quantity"]), Decimal(actual["total"])), (Decimal(1), Decimal(99)))


if __name__ == "__main__":
    unittest.main()
