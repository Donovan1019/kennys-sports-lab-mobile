"""Regression tests for independent NCAAB historical game counting."""
import unittest
from datetime import datetime, timedelta, timezone
from scripts.build_ncaab_ml_predictions import build

NOW = datetime(2026, 11, 16, tzinfo=timezone.utc)

def game(day, home, away, hp, ap):
    return {"date": (NOW - timedelta(days=day)).isoformat(),
            "status": {"type": {"completed": True}},
            "competitions": [{"competitors": [
                {"homeAway": "home", "score": str(hp),
                 "team": {"displayName": home, "shortDisplayName": home}},
                {"homeAway": "away", "score": str(ap),
                 "team": {"displayName": away, "shortDisplayName": away}}
            ]}]}

class TestNCAABGameCounting(unittest.TestCase):
    def test_three_actual_games_required_not_duplicate_name_aliases(self):
        odds = {"odds": [{"event_id": "test1", "market": "h2h",
                          "event": "Away College @ Home College",
                          "commence_time": (NOW + timedelta(days=1)).isoformat()}]}
        two_games = [game(2, "Home College", "Away College", 70, 65),
                     game(1, "Home College", "Away College", 80, 75)]
        self.assertEqual(build(odds, two_games, NOW)["predictions"], [])
        three_games = two_games + [game(3, "Home College", "Away College", 75, 72)]
        rows = build(odds, three_games, NOW)["predictions"]
        self.assertEqual(len(rows), 2)
        self.assertEqual({r["sample_games"] for r in rows}, {3})
        self.assertAlmostEqual(sum(r["win_probability"] for r in rows), 1.0)

if __name__ == "__main__":
    unittest.main()
