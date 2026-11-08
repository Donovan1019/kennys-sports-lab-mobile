import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from scripts.join_nfl_pregame_results import join

class PregameJoinTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "feed").mkdir()
        self.archive = self.root / "archive" / "nfl_moneyline" / "inputs"
        self.archive.mkdir(parents=True)
        self.final = {"event_id": "401", "date": "2026-11-08T18:00:00Z", "away": "Away", "home": "Home", "away_score": 17, "home_score": 24}
        self.game = {"event_id": "401", "commence_time": "2026-11-08T18:00:00Z", "away": "Away", "home": "Home",
                     "teams": [{"score_history": [{"date": "2026-11-01T18:00:00Z", "scored": 10, "allowed": 14}]}]}
        self.write()
    def write(self):
        (self.root / "feed" / "nfl_completed_games.json").write_text(json.dumps({"games": [self.final]}))
        (self.archive / "20261108T110000Z.json").write_text(json.dumps({"source_timestamp": "2026-11-08T11:00:00Z", "games": [self.game]}))
    def test_exact_event_id_join(self):
        r = join(self.root)
        self.assertEqual(r["joined_snapshots"], 1)
        self.assertEqual(r["rows"][0]["winner"], "home")
        self.assertTrue(r["rows"][0]["evaluation_only"])
    def test_no_match_is_not_invented(self):
        self.final["event_id"] = "other"
        self.write()
        self.assertEqual(join(self.root)["joined_snapshots"], 0)
    def test_future_history_rejected(self):
        self.game["teams"][0]["score_history"][0]["date"] = "2026-11-09T18:00:00Z"
        self.write()
        with self.assertRaises(ValueError):
            join(self.root)
    def test_team_mismatch_rejected(self):
        self.final["away"] = "Different"
        self.write()
        with self.assertRaises(ValueError):
            join(self.root)
    def test_non_pregame_rejected(self):
        self.game["commence_time"] = "2026-11-08T10:00:00Z"
        self.write()
        with self.assertRaises(ValueError):
            join(self.root)

if __name__ == "__main__":
    unittest.main()
