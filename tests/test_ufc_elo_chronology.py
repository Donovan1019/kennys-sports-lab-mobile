#!/usr/bin/env python3
"""Regression tests for point-in-time UFC Elo evaluation."""
import unittest
from scripts.ufc_elo_baseline import build

def fight(event, fight_id, date, winner, loser):
    return {"event_id":event,"fight_id":fight_id,"event_date":date,"winner":winner,"loser":loser,"winner_verified":True}

class TestEloChronology(unittest.TestCase):
    def test_same_event_uses_frozen_ratings(self):
        rows=[
            fight("1","a","2024-01-01T00:00:00Z","A","B"),
            fight("1","b","2024-01-01T00:00:00Z","C","D"),
            fight("2","c","2024-02-01T00:00:00Z","A","C"),
            fight("2","d","2024-02-01T00:00:00Z","B","D"),
        ]
        result=build(rows,minimum_history=1)
        self.assertEqual(result["historical_bouts_used"],4)
        self.assertEqual(result["pre_update_evaluated_fights"],2)
        self.assertEqual(result["holdout_evaluated_fights"],1)
        self.assertFalse(result["bet_eligible"])
        self.assertEqual(result["holdout_status"],"INSUFFICIENT_SAMPLE")
        self.assertEqual(result["holdout_start"],"2024-02-01T00:00:00+00:00")
    def test_same_event_different_fight_times_do_not_leak(self):
        rows=[fight("card","first","2024-01-01T01:00:00Z","A","B"),
              fight("card","second","2024-01-01T02:00:00Z","A","C")]
        report=build(rows,minimum_history=1)
        self.assertEqual(report["all_pre_update_evaluated_fights"],2)
        self.assertAlmostEqual(report["all_pre_update_forecasts"][1]["winner_probability"],0.5)
        self.assertEqual(report["pre_update_evaluated_fights"],0)
    def test_duplicate_fight_is_not_double_counted(self):
        rows=[fight("1","a","2024-01-01T00:00:00Z","A","B")]*2
        result=build(rows)
        self.assertEqual(result["historical_bouts_used"],1)
        self.assertEqual(result["all_pre_update_evaluated_fights"],1)
    def test_unverified_winner_is_excluded(self):
        row=fight("1","a","2024-01-01T00:00:00Z","A","B")
        row["winner_verified"]=False
        self.assertEqual(build([row])["historical_bouts_used"],0)
if __name__=="__main__":
    unittest.main()
