import unittest
from scripts.nba_player_walkforward_research import evaluate

class WalkForwardTests(unittest.TestCase):
    def test_never_promotes_research(self):
        games=[{"date":f"2026-01-{i:02d}","game_id":str(i),"season":"2025-26","season_type":"regular","values":{"Points":i}} for i in range(1,13)]
        result=evaluate({"source":"espn-public-boxscore","sport":"nba","players":[{"id":"1","games":games}]})
        self.assertEqual(result["status"],"research_only")
        self.assertFalse(result["promotion_approved"])
        self.assertEqual(result["markets"]["Points"]["samples"],4)
        self.assertEqual(result["fixed_reference_threshold_probability_research"]["Points"]["9.5"]["samples"],4)
        self.assertFalse(result["promotion_approved"])
        season=result["fixed_reference_threshold_probability_by_season"]["Points"]["2025-26"]["9.5"]
        self.assertEqual(season["samples"],4)
        self.assertIn("walkforward_brier",season)
        self.assertIn("constant_50pct_brier",season)
        self.assertIsInstance(season["beats_constant_50pct"],bool)
        self.assertEqual(result["markets"]["Points"]["mae_last_10"],5.125)
    def test_requires_verified_source(self):
        with self.assertRaises(ValueError):
            evaluate({"source":"unverified","sport":"nba","players":[]})

if __name__=="__main__":unittest.main()
