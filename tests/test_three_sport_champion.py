import unittest
from scripts.three_sport_champion import SPORTS,capture,evaluate

class ThreeSportChampionTests(unittest.TestCase):
    def test_all_sports_included(self):
        self.assertEqual(set(SPORTS),{"basketball_nba","icehockey_nhl","americanfootball_nfl"})
    def test_missing_quote_timestamp_rejected(self):
        ledger={"forecasts":[{"forecast_id":"a","event_id":"e","forecast_at":"2026-10-21T12:00:00Z","event_start":"2026-10-21T20:00:00Z"}]}
        quotes={"events":[{"event_id":"e","home_consensus_no_vig":.55,"bookmaker_count":3}]}
        self.assertEqual(capture({},ledger,quotes)["baselines"],[])
        quotes["events"][0]["verified_quote_at"]="2026-10-21T11:00:00Z"
        self.assertEqual(len(capture({},ledger,quotes)["baselines"]),1)
        quotes["events"][0]["verified_quote_at"]="2026-10-21T13:00:00Z"
        self.assertEqual(capture({},ledger,quotes)["baselines"],[])
    def test_no_market_edge_without_verified_pair(self):
        outcomes={"scored":[{"forecast_id":"a","home_probability":.7,"home_won":1}]}
        baselines={"baselines":[{"forecast_id":"a","home_probability":.6,"status":"unverified_quote_time_research_only"}]}
        result=evaluate(outcomes,baselines)
        self.assertEqual(result["verified_paired_games"],0)
        self.assertFalse(result["promotion_approved"])
    def test_verified_pair(self):
        outcomes={"scored":[{"forecast_id":"a","home_probability":.7,"home_won":1}]}
        baselines={"baselines":[{"forecast_id":"a","home_probability":.6,"status":"verified_pregame_quote"}]}
        result=evaluate(outcomes,baselines)
        self.assertEqual(result["verified_paired_games"],1)
        self.assertLess(result["model_brier"],result["market_brier"])
        self.assertFalse(result["promotion_approved"])
if __name__=="__main__":
    unittest.main()
