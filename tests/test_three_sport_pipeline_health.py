import json
import tempfile
from datetime import datetime, timezone
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

    def test_stale_forecasts_with_active_markets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for sport in SPORTS:
                for suffix, payload in (("forecast_ledger", {"forecasts":[{"created_at":"2026-09-01T00:00:00Z"}]}),
                                        ("forecast_outcomes", {"scored":[]}),
                                        ("market_consensus", {"events":[{"event_id":"active"}]}),
                                        ("market_baseline_ledger", {"baselines":[]})):
                    (root / f"{sport}_{suffix}.json").write_text(json.dumps(payload))
            result = audit(root, datetime(2026,10,21,tzinfo=timezone.utc))
            self.assertEqual(result["status"], "attention_required")
            self.assertIn("stale_forecasts_over_8_days_with_market_events", result["sports"][0]["issues"])

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
