import copy
import unittest
from scripts.replay_nba_ml_oct28 import replay, PICKS

def fixture():
    return {"status": "ok", "captured_at": "2026-10-28T22:03:01Z",
            "rows": [{"selection": team, "bookmaker": "fanduel", "event_id": str(i),
                      "quote_updated_at": "2026-10-28T22:02:40Z",
                      "commence_time": "2026-10-28T23:10:00Z",
                      "price": -120, "model_probability": .6}
                     for i, team in enumerate(PICKS)]}

class ReplayTests(unittest.TestCase):
    def test_winners_and_brier(self):
        result = replay(fixture())
        self.assertEqual((result["wins"], result["legs"]), (1, 5))
        self.assertAlmostEqual(result["mean_brier"], .28)

    def test_reject_post_tipoff(self):
        data = fixture()
        data["rows"][0]["quote_updated_at"] = "2026-10-28T23:11:00Z"
        with self.assertRaises(ValueError):
            replay(data)

    def test_reject_missing_and_duplicate_quotes(self):
        data = fixture()
        data["rows"].pop()
        with self.assertRaises(ValueError):
            replay(data)
        data = fixture()
        data["rows"].append(copy.deepcopy(data["rows"][0]))
        with self.assertRaises(ValueError):
            replay(data)

if __name__ == "__main__":
    unittest.main()
