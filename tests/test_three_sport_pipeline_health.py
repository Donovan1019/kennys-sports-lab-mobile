import json
import tempfile
import unittest
from pathlib import Path
from scripts.three_sport_pipeline_health import audit, SPORTS

class PipelineHealthTests(unittest.TestCase):
    def test_missing_inputs_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = audit(Path(tmp))
            self.assertEqual(result["status"], "attention_required")
            self.assertEqual(len(result["sports"]), 3)
            self.assertIn("missing_forecast_ledger", result["sports"][0]["issues"])

    def test_pending_games_are_not_false_alarm(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for sport in SPORTS:
                for suffix, payload in (("forecast_ledger", {"forecasts":[{"event_id":"upcoming"}]}),
                                        ("forecast_outcomes", {"scored":[]}),
                                        ("market_consensus", {"events":[]}),
                                        ("market_baseline_ledger", {"baselines":[]})):
                    (root / f"{sport}_{suffix}.json").write_text(json.dumps(payload))
            result = audit(root)
            self.assertEqual(result["status"], "operational")
            self.assertEqual(result["paid_api_calls"], 0)

if __name__ == "__main__":
    unittest.main()
