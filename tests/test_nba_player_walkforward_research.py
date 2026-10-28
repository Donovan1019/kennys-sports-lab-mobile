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
        self.assertIn(audit["selected_window"],["5","10","20","all","blend_25","blend_50","blend_75"])
        self.assertIn("blend_50",result["window_comparison_by_season"]["Points"]["2026-27"])
        self.assertFalse(audit["bet_eligible"])
        self.assertFalse(audit["holdout_gate_passed"])  # Four holdout games cannot pass 1,000-game gate.
        self.assertFalse(audit["training_stability_passed"])
        self.assertFalse(audit["research_validation_gate_passed"])
        self.assertIn("INSUFFICIENT_HOLDOUT_SAMPLES",audit["rejection_reasons"])
        self.assertIn("TRAINING_PERIOD_INSTABILITY_OR_INSUFFICIENT_SAMPLES",audit["rejection_reasons"])
        self.assertEqual(len(audit["training_chronological_halves"]),2)
        self.assertFalse(result["promotion_approved"])
        self.assertFalse(result["promotion_approved"])
        self.assertEqual(result["window_comparison_by_season"]["Points"]["2026-27"]["all"]["samples"],4)
    def test_minutes_workload_requires_prior_minutes_and_never_promotes(self):
        games=[{"date":f"2026-01-{i:02d}","game_id":str(i),"season":"2025-26",
                "season_type":"regular","values":{"Points":float(i),"Minutes":20.0}}
               for i in range(1,13)]
        result=evaluate({"source":"espn-public-boxscore","sport":"nba","players":[{"id":"1","games":games}]})
        audit=result["window_comparison_by_season"]["Points"]["2025-26"]["minutes_adjusted"]
        self.assertEqual(audit["samples"],4)
        self.assertEqual(audit["mae"],5.125)
        recent=result["recent_minutes_rate_matched_sample_audit"]["Points"]["2025-26"]
        self.assertEqual(recent["samples"],4)
        self.assertEqual(recent["recent_rate_mae"],5.125)
        self.assertFalse(recent["bet_eligible"])
        self.assertFalse(result["recent_minutes_rate_selection_eligible"])
        segments=result["recent_minutes_workload_segment_audit"]["Points"]["2025-26"]
        self.assertEqual(sum(v["samples"] for k,v in segments.items() if not k.startswith("change:")),recent["samples"])
        self.assertEqual(sum(v["samples"] for k,v in segments.items() if k.startswith("change:")),recent["samples"])
        self.assertTrue(all(not v["bet_eligible"] for v in segments.values()))
        pair=result["minutes_adjusted_matched_sample_audit"]["Points"]["2025-26"]
        self.assertEqual(pair["samples"],4)
        self.assertEqual(pair["minutes_mae"],pair["all_prior_mae_same_samples"])
        self.assertEqual(pair["minutes_wins"]+pair["all_prior_wins"]+pair["ties"],4)
        self.assertFalse(pair["passes_holdout_improvement_threshold"])
        self.assertFalse(pair["bet_eligible"])
        self.assertFalse(result["minutes_adjusted_selection_eligible"])
        self.assertFalse(result["promotion_approved"])
    def test_missing_minutes_does_not_generate_minutes_forecast(self):
        games=[{"date":f"2026-01-{i:02d}","game_id":str(i),"season":"2025-26",
                "season_type":"regular","values":{"Points":float(i)}}
               for i in range(1,13)]
        result=evaluate({"source":"espn-public-boxscore","sport":"nba","players":[{"id":"1","games":games}]})
        self.assertNotIn("minutes_adjusted",result["window_comparison_by_season"]["Points"]["2025-26"])
        self.assertEqual(result["minutes_workload_data_coverage"]["Points"]["missing_prior_minutes"],4)
        self.assertNotIn("Points",result["minutes_adjusted_matched_sample_audit"])
        self.assertNotIn("Points",result["recent_minutes_rate_matched_sample_audit"])
    def test_requires_verified_source(self):
        with self.assertRaises(ValueError):
            evaluate({"source":"unverified","sport":"nba","players":[]})

if __name__=="__main__":unittest.main()
