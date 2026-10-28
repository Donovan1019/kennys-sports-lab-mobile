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
    def test_train_only_window_selection_and_holdout(self):
        games=[]
        for i in range(1,15):
            games.append({"date":f"2026-01-{i:02d}","game_id":str(i),
                "season":"2025-26","season_type":"regular","values":{"Points":i}})
        for i in range(1,5):
            games.append({"date":f"2026-10-{i:02d}","game_id":f"h{i}",
                "season":"2026-27","season_type":"regular","values":{"Points":20+i}})
        result=evaluate({"source":"espn-public-boxscore","sport":"nba",
            "players":[{"id":"1","games":games}]})
        audit=result["training_selected_window_holdout_audit"]["Points"]
        self.assertEqual(audit["training_season"],"2025-26")
        self.assertEqual(audit["holdout_season"],"2026-27")
        self.assertEqual(audit["holdout_samples"],4)
        self.assertIn(audit["selected_window"],["5","10","20","all"])
        self.assertFalse(result["promotion_approved"])
        self.assertEqual(result["window_comparison_by_season"]["Points"]["2026-27"]["all"]["samples"],4)
    def test_requires_verified_source(self):
        with self.assertRaises(ValueError):
            evaluate({"source":"unverified","sport":"nba","players":[]})

if __name__=="__main__":unittest.main()
