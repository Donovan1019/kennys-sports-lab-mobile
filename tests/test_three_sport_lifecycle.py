import unittest
from scripts.three_sport_lifecycle import inspect
from scripts.three_sport_champion import SPORTS

class LifecycleTests(unittest.TestCase):
    def test_all_sports(self):
        self.assertEqual(len(SPORTS),3)
        for sport in SPORTS:
            self.assertEqual(inspect(sport,{})["status"],"awaiting_verified_pairs")
    def test_explicit_blockers(self):
        r=inspect("icehockey_nhl",{"forecast_ledger":{"forecasts":[{"forecast_id":"f"}]},
             "market_consensus":{"events":[{"event_id":"e"}]}})
        self.assertIn("no_verified_quote_time_matched_baselines",r["blockers"])
        self.assertIn("no_verified_completed_forecast_matches",r["blockers"])
    def test_paired_ready(self):
        r=inspect("basketball_nba",{"champion_challenger":{"verified_paired_games":4}})
        self.assertEqual(r["status"],"paired_evaluation_available")
        self.assertEqual(r["verified_paired_games"],4)
if __name__=="__main__":
    unittest.main()
