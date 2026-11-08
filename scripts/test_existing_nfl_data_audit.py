import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from scripts.audit_existing_nfl_data import audit

NOW = dt.datetime(2026, 11, 8, 12, tzinfo=dt.timezone.utc)

class ExistingDataAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "feed").mkdir()
    def put(self, filename, data):
        (self.root / "feed" / filename).write_text(json.dumps(data))
    def test_reuses_completed_results_and_flags_stale_odds(self):
        self.put("nfl_completed_games.json", {"fetched_at": NOW.isoformat(), "games": [
            {"event_id": "1", "date": "2026-11-05T01:00:00Z", "away": "A", "home": "B", "away_score": 10, "home_score": 20}]})
        self.put("independent_game_inputs.json", {"source_games_fetched_at": NOW.isoformat(), "games": [
            {"teams": [{"score_history": [{"date": "2026-11-05T01:00:00Z", "scored": 10, "allowed": 20}]}]}]})
        self.put("americanfootball_nfl.json", {"fetched_at": "2026-11-01T11:00:00Z", "odds": [
            {"market": "h2h", "bookmaker": "draftkings"}]})
        r = audit(self.root, NOW)
        self.assertEqual(r["sources"]["completed_games"]["valid_final_scores"], 1)
        self.assertEqual(r["sources"]["schedule_inputs"]["season_classified_rows"], 0)
        self.assertEqual(r["sources"]["sportsbook_odds"]["status"], "STALE")
        self.assertEqual(r["sources"]["sportsbook_odds"]["nfl_moneylines"], 1)
        self.assertEqual(len(r["warnings"]), 2)
    def test_missing_feeds(self):
        r = audit(self.root, NOW)
        self.assertTrue(all(x["status"] == "MISSING" for x in r["sources"].values()))

if __name__ == "__main__":
    unittest.main()
