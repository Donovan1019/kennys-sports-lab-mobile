#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_nfl_prop_archive_health import inspect
class ArchiveHealthTests(unittest.TestCase):
    def test_empty_archive_is_blocked(self):
        d=inspect({"forecasts":[]},[],{"status":"PARTIAL","captured_events":0})
        self.assertEqual(d["pregame_forecasts_archived"],0)
        self.assertEqual(d["bet_eligibility"],"BLOCKED")
    def test_awaiting_grade(self):
        d=inspect({"forecasts":[{"forecast_id":"a","market":"player_pass_yds"}]},[],{})
        self.assertEqual(d["archived_forecasts_awaiting_verified_grade"],1)
    def test_duplicate_id_rejected(self):
        with self.assertRaises(ValueError):
            inspect({"forecasts":[{"forecast_id":"a"},{"forecast_id":"a"}]},[],{})
    def test_missing_schema_rejected(self):
        with self.assertRaises(ValueError):
            inspect({},[],{})
    def test_verified_forward_brier(self):
        f={"forecast_id":"a","market":"player_pass_yds","model_probability":0.8,
           "forecast_at":"2026-11-01T12:00:00Z","kickoff":"2026-11-01T18:00:00Z"}
        d=inspect({"forecasts":[f]},[{"forecast_id":"a","outcome_verified":True,"over_hit":True}],{})
        self.assertEqual(d["matched_verified_forward_grades"],1)
        self.assertAlmostEqual(d["forward_brier_score"],0.04)
        self.assertFalse(d["forward_calibration_approved"])
    def test_reject_leakage_and_unmatched_grades(self):
        f={"forecast_id":"a","model_probability":0.8,"forecast_at":"2026-11-01T20:00:00Z","kickoff":"2026-11-01T18:00:00Z"}
        d=inspect({"forecasts":[f]},[{"forecast_id":"a","outcome_verified":True,"over_hit":True},
          {"forecast_id":"other","outcome_verified":True,"over_hit":False}],{})
        self.assertEqual(d["matched_verified_forward_grades"],0)
        self.assertIsNone(d["forward_brier_score"])

if __name__=="__main__":unittest.main()
