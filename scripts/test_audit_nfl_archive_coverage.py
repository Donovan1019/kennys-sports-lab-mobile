import json
import tempfile
import unittest
from pathlib import Path
from scripts.audit_nfl_archive_coverage import audit

class ArchiveCoverageTests(unittest.TestCase):
    def test_no_archive_reports_zero_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "feed").mkdir()
            (root / "feed/nfl_completed_games.json").write_text(json.dumps({"games": [{"event_id": "1", "date": "2026-11-01T18:00:00Z", "away": "A", "home": "B", "away_score": 10, "home_score": 20}]}))
            result = audit(root)
            self.assertEqual(result["completed_results"], 1)
            self.assertEqual(result["unique_completed_games_with_pregame_inputs"], 0)
            self.assertEqual(result["status"], "NO_MATCHED_PREGAME_ARCHIVES")
            self.assertFalse(result["calibrated_accuracy_available"])
    def test_real_pregame_snapshot_joins(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "feed").mkdir()
            archive = root / "archive/nfl_moneyline/inputs"
            archive.mkdir(parents=True)
            (root / "feed/nfl_completed_games.json").write_text(json.dumps({"games": [{"event_id": "1", "date": "2026-11-01T18:00:00Z", "away": "A", "home": "B", "away_score": 10, "home_score": 20}]}))
            (archive / "pregame.json").write_text(json.dumps({"source_timestamp": "2026-10-31T18:00:00Z", "games": [{"event_id": "1", "commence_time": "2026-11-01T18:00:00Z", "away": "A", "home": "B", "teams": []}]}))
            result = audit(root)
            self.assertEqual(result["unique_completed_games_with_pregame_inputs"], 1)
            self.assertFalse(result["historical_predictions_verified"])

if __name__ == "__main__":
    unittest.main()
