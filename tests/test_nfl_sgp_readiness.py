import sys,unittest
from unittest.mock import patch
from datetime import datetime,timezone,timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from audit_nfl_sgp_readiness import audit
class Readiness(unittest.TestCase):
    def test_fail_closed(self):
        r=audit()
        self.assertFalse(r["betting_eligible"])
        self.assertFalse(r["checks"]["validated_joint_model_and_ev"])
        self.assertIn(r["status"],("BLOCKED","REVIEW_REQUIRED"))
    def test_stale_injury_sources_do_not_verify(self):
        now=datetime.now(timezone.utc)
        stale=(now-timedelta(hours=7)).isoformat()
        injury={"ingestion_status":"VERIFIED","verified_player_reports":9,"checked_at":stale}
        espn={"player_ingestion_enabled":True,"verified_player_reports":9,"checked_at":stale}
        from audit_nfl_sgp_readiness import load as original_load
        def mocked_load(path):
            if path=="feed/nfl_injury_source_health.json":return injury
            if path=="feed/nfl_injury_espn_discovery.json":return espn
            return original_load(path)
        with patch("audit_nfl_sgp_readiness.load",side_effect=mocked_load):
            self.assertFalse(audit()["checks"]["verified_player_injury_reports_present"])
    def test_missing_injury_timestamps_do_not_verify(self):
        from audit_nfl_sgp_readiness import load as original_load
        def mocked_load(path):
            if path=="feed/nfl_injury_source_health.json":return {"ingestion_status":"VERIFIED","verified_player_reports":9}
            if path=="feed/nfl_injury_espn_discovery.json":return {"player_ingestion_enabled":True,"verified_player_reports":9}
            return original_load(path)
        with patch("audit_nfl_sgp_readiness.load",side_effect=mocked_load):
            self.assertFalse(audit()["checks"]["verified_player_injury_reports_present"])
    def test_identity_count(self):
        r=audit()
        self.assertLessEqual(r["logs_with_game_identity"],r["player_game_logs"])
    def test_market_flags(self):
        for market in audit()["market_calibration"].values():
            self.assertIsInstance(market["eligible_for_live_use"],bool)
if __name__=="__main__":unittest.main()
