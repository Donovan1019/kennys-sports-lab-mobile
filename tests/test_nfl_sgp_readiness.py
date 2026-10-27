import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from audit_nfl_sgp_readiness import audit
class Readiness(unittest.TestCase):
    def test_fail_closed(self):
        r=audit()
        self.assertFalse(r["betting_eligible"])
        self.assertFalse(r["checks"]["validated_joint_model_and_ev"])
        self.assertIn(r["status"],("BLOCKED","REVIEW_REQUIRED"))
    def test_identity_count(self):
        r=audit()
        self.assertLessEqual(r["logs_with_game_identity"],r["player_game_logs"])
    def test_market_flags(self):
        for market in audit()["market_calibration"].values():
            self.assertIsInstance(market["eligible_for_live_use"],bool)
if __name__=="__main__":unittest.main()
