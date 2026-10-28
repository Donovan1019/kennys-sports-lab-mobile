import datetime as dt
import unittest
from scripts.archive_nba_ml_odds import snapshot
from scripts.fetch_nba_ml_schedule_evidence import parse
from scripts.audit_nba_ml_betting_readiness import audit
NOW=dt.datetime(2026,10,28,22,tzinfo=dt.timezone.utc)
class NBADataCoverageTests(unittest.TestCase):
 def test_archive_captures_only_valid_pregame_quote(self):
  odds={"status":"ok","fetched_at":"2026-10-28T21:30:00Z","odds":[{"market":"h2h","event_id":"1","event":"Miami Heat @ Atlanta Hawks","commence_time":"2026-10-28T23:10:00Z","updated_at":"2026-10-28T21:29:00Z","selection":"Miami Heat","price":+120,"bookmaker":"fanduel"}]}
  model={"status":"validated","generated_at":"2026-10-28T21:30:00Z","predictions":[{"event_id":"1","team":"Miami Heat","win_probability":0.5}]}
  out=snapshot(odds,model,NOW)
  self.assertEqual(len(out["rows"]),1)
  self.assertFalse(out["historical_backtest_validated"])
 def test_stale_archive_fails_closed(self):
  self.assertEqual(snapshot({}, {}, NOW)["status"],"unavailable")
 def test_empty_schedule_does_not_claim_lineups(self):
  out=parse({"events":[]},NOW)
  self.assertFalse(out["confirmed_lineups"])
  self.assertFalse(out["injury_status_verified"])
 def test_schedule_and_archive_are_not_betting_certification(self):
  schedule={"status":"ok","fetched_at":"2026-10-28T21:30:00Z"}
  archive={"status":"ok","captured_at":"2026-10-28T21:30:00Z","rows":[{"event_id":"1"}]}
  out=audit({}, {}, NOW,schedule,archive)
  self.assertTrue(out["checks"]["schedule_evidence_fresh"])
  self.assertTrue(out["checks"]["pregame_odds_archiving_active"])
  self.assertFalse(out["checks"]["injury_lineup_rest_confirmed"])
  self.assertEqual(out["status"],"not_bet_eligible")
if __name__=="__main__":unittest.main()
