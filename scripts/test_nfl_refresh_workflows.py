#!/usr/bin/env python3
"""Guard NFL scheduled workflows against malformed YAML and missing archive wiring."""
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]

class WorkflowIntegrityTests(unittest.TestCase):
    def check_workflow(self, filename, kind):
        text = (ROOT / ".github" / "workflows" / filename).read_text()
        self.assertNotIn(r"\n", text, "literal escaped newline in workflow")
        workflow = yaml.safe_load(text)
        self.assertIsInstance(workflow, dict)
        self.assertIn("jobs", workflow)
        self.assertIn("refresh", workflow["jobs"])
        steps = workflow["jobs"]["refresh"]["steps"]
        commands = [str(s.get("run", "")) for s in steps]
        self.assertTrue(any("archive_nfl_moneyline_snapshots.py " + kind in c for c in commands))
        self.assertTrue(any("git add" in c and "archive/nfl_moneyline/" + kind in c for c in commands))
        self.assertTrue(any("scripts/" + ("refresh_nfl_moneyline_inputs.py" if kind == "inputs" else "fetch_odds.py") in c for c in commands))
        self.assertTrue(any("schedule" in str(k) for k in workflow.keys()))

    def test_inputs_workflow(self):
        self.check_workflow("nfl-moneyline-inputs.yml", "inputs")

    def test_odds_workflow(self):
        self.check_workflow("refresh-odds.yml", "odds")

if __name__ == "__main__":
    unittest.main()
