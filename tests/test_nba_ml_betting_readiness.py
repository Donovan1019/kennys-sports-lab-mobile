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

class EvidenceProvenanceTests(unittest.TestCase):
 def test_research_only_never_certifies(self):
  evidence={"outcome_market":{"status":"research_only","historical_pregame_odds_backtest_verified":True,"closing_line_value_verified":True}}
  out=audit({}, {}, NOW, evidence=evidence)
  self.assertFalse(out["checks"]["historical_pregame_odds_backtest"])
  self.assertFalse(out["checks"]["closing_line_value_verified"])
  self.assertIn("historical_pregame_odds_backtest",out["outstanding_checks"])
  self.assertEqual(out["check_details"]["closing_line_value_verified"]["status"],"UNVERIFIED")
 def test_missing_or_stale_verification_rejected(self):
  evidence={"outcome_market":{"status":"verified","verification_id":"audit-1","verified_at":"2026-10-27T12:00:00Z","closing_line_value_verified":True}}
  out=audit({}, {}, NOW, evidence=evidence)
  self.assertFalse(out["checks"]["closing_line_value_verified"])
 def test_independent_verification_visible_but_no_auto_promotion(self):
  evidence={"outcome_market":{"status":"verified","verification_id":"audit-1","verified_at":"2026-10-28T21:00:00Z","closing_line_value_verified":True}}
  out=audit({}, {}, NOW, evidence=evidence)
  self.assertTrue(out["checks"]["closing_line_value_verified"])
  self.assertEqual(out["status"],"not_bet_eligible")

class ResearchRiskTests(unittest.TestCase):
 def test_negative_research_roi_is_disclosed_without_certification(self):
  evidence={"outcome_market":{"status":"research_only","paper_roi":-0.386712,"paper_selected_events":26}}
  out=audit({}, {}, NOW, evidence=evidence)
  self.assertEqual(out["research_warning"]["paper_selected_events"],26)
  self.assertLess(out["research_warning"]["paper_roi"],0)
  self.assertEqual(out["status"],"not_bet_eligible")
 def test_missing_research_roi_is_not_invented(self):
  out=audit({}, {}, NOW, evidence={"outcome_market":{"status":"research_only"}})
  self.assertNotIn("research_warning",out)
