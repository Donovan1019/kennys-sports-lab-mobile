import unittest
from unittest.mock import patch
from scripts.audit_nba_ml_possession_backtest import evaluate
class TestPossessionBacktest(unittest.TestCase):
 def test_missing_history_fails_closed(self):
  r=evaluate([])
  self.assertEqual(r["status"],"insufficient_evidence")
  self.assertFalse(r["betting_eligible"])
 def test_incomplete_game_rejected(self):
  r=evaluate([{"id":"x","date":"2026-01-01T00:00:00Z","home":"A","away":"B"}])
  self.assertEqual(r["evaluated_games"],0)
 def test_insufficient_sample_has_no_calibration(self):
  r=evaluate([],min_holdout=1)
  self.assertNotIn("log_loss",r)
  self.assertNotIn("calibration_bins",r)
class TestCalibrationRegression(unittest.TestCase):
 def test_calibration_and_baseline_from_chronological_predictions(self):
  games=[]
  for i in range(4):
   games.append({"id":str(i),"date":"2026-01-0"+str(i+1)+"T00:00:00Z","home":"H","away":"A","box":{"H":{"points":110 if i%2==0 else 90},"A":{"points":100}}})
  with patch("scripts.audit_nba_ml_possession_backtest.metrics",return_value={}),patch("scripts.audit_nba_ml_possession_backtest.simulate",side_effect=[
   {"status":"diagnostic_only","home_full_game_win_probability":p} for p in (.7,.3,.8,.2)]):
   r=evaluate(games,min_history=0,min_holdout=4)
  self.assertEqual(r["evaluated_games"],4)
  self.assertEqual(r["status"],"descriptive_only")
  self.assertAlmostEqual(r["brier"],.065,places=6)
  self.assertEqual(r["baseline"]["constant_brier"],.25)
  self.assertEqual(sum(x["count"] for x in r["calibration_bins"]),4)
  self.assertTrue(all(0<=b["observed_wilson_95"][0]<=b["observed_win_rate"]<=b["observed_wilson_95"][1]<=1 for b in r["calibration_bins"]))
  self.assertGreater(r["log_loss"],0)
  self.assertEqual(r["calibration_coverage"]["binned_games"],4)
  self.assertEqual(r["calibration_coverage"]["excluded_games"],0)
  self.assertEqual(r["calibration_coverage"]["total_evaluated"],4)
  self.assertFalse(r["betting_eligible"])

 def test_invalid_probability_is_excluded(self):
  games=[{"id":str(i),"date":"2026-01-0"+str(i+1)+"T00:00:00Z","home":"H","away":"A","box":{"H":{"points":110},"A":{"points":100}}} for i in range(2)]
  with patch("scripts.audit_nba_ml_possession_backtest.metrics",return_value={}),patch("scripts.audit_nba_ml_possession_backtest.simulate",side_effect=[
   {"status":"diagnostic_only","home_full_game_win_probability":float("nan")},
   {"status":"diagnostic_only","home_full_game_win_probability":.7}]):
   r=evaluate(games,min_history=0,min_holdout=2)
  self.assertEqual(r["evaluated_games"],1)
  self.assertEqual(r["status"],"insufficient_evidence")
  self.assertNotIn("log_loss",r)
if __name__=="__main__":unittest.main()
