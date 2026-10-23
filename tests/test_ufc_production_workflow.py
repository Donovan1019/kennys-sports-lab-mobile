from pathlib import Path
import unittest

class UFCProductionWorkflowTests(unittest.TestCase):
    def test_daily_workflow_uses_module_import_and_stages_new_files(self):
        workflow=Path(".github/workflows/ufc-card-refresh.yml").read_text()
        self.assertIn("python -m scripts.ufc_automated_backfill",workflow)
        self.assertIn("python -m scripts.ufc_holdout_readiness",workflow)
        self.assertIn("git add feed/ufc_research.json",workflow)
        self.assertIn("git diff --cached --quiet",workflow)
        self.assertIn("schedule:",workflow)
        self.assertNotIn("python scripts/ufc_automated_backfill.py",workflow)

if __name__=="__main__":
    unittest.main()
