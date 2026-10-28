import datetime as dt
import unittest
from scripts.audit_nba_ml_betting_readiness import audit
NOW=dt.datetime(2026,10,28,22,tzinfo=dt.timezone.utc)
class BettingReadinessTests(unittest.TestCase):
 def test_fresh_model_and_odds_do_not_imply_betting_ready(self):
  odds={"status":"ok","fetched_at":"2026-10-28T21:00:00Z"}
  model={"status":"validated","calibration_passed":True,"generated_at":"2026-10-28T21:00:00Z"}
  out=audit(odds,model,NOW)
  self.assertEqual(out["status"],"not_bet_eligible")
  self.assertTrue(out["checks"]["odds_fresh"])
  self.assertTrue(out["checks"]["model_fresh_and_calibrated"])
  self.assertFalse(out["checks"]["historical_pregame_odds_backtest"])
  self.assertFalse(out["checks"]["executable_same_book_parlay_quote"])
 def test_stale_or_missing_inputs_fail_closed(self):
  out=audit({}, {}, NOW)
  self.assertFalse(out["checks"]["odds_fresh"])
  self.assertFalse(out["checks"]["model_fresh_and_calibrated"])
if __name__=="__main__":unittest.main()
