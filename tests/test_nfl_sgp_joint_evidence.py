import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from nfl_sgp_joint_evidence import validate

BASE = dict(event_id="game-1", player_id="p1", market="receiving_yards",
            line=49.5, side="over", forecast_at="2026-10-25T12:00:00-04:00",
            kickoff_at="2026-10-25T13:00:00-04:00", outcome=65, probability=.65, slip_id="slip-a")

class TestSGPJointEvidence(unittest.TestCase):
    def test_same_game_and_baseline(self):
        b = dict(BASE, player_id="p2", probability=.7, outcome=35)
        result = validate([BASE,b])
        self.assertEqual(result["same_game_multi_leg_events"],1)
        self.assertAlmostEqual(result["independent_joint_baseline_brier"], (.65*.7)**2)
        self.assertFalse(result["betting_eligible"])
        self.assertIsNone(result["joint_model_brier"])
    def test_same_game_different_slips_not_joined(self):
        other=dict(BASE, player_id="p2", slip_id="slip-b")
        self.assertEqual(validate([BASE,other])["same_game_multi_leg_events"],0)
    def test_missing_slip_id_does_not_create_joint(self):
        a=dict(BASE); a.pop("slip_id")
        b=dict(a,player_id="p2")
        result=validate([a,b])
        self.assertEqual(result["same_game_multi_leg_events"],0)
        self.assertEqual(sum(x["reason"]=="missing_slip_id_for_joint_evaluation" for x in result["rejected_rows"]),2)
    def test_repeated_market_within_slip_is_rejected(self):
        other=dict(BASE, line=54.5, probability=.6)
        result=validate([BASE,other])
        self.assertEqual(result["same_game_multi_leg_events"],0)
        self.assertIn("repeated_player_market_in_slip",[x["reason"] for x in result["rejected_rows"]])
    def test_conflicting_kickoff_rejected(self):
        other=dict(BASE,player_id="p2",kickoff_at="2026-10-25T14:00:00-04:00")
        result=validate([BASE,other])
        self.assertEqual(result["same_game_multi_leg_events"],0)
        self.assertIn("conflicting_event_kickoff",[x["reason"] for x in result["rejected_rows"]])
    def test_cross_game_not_joined(self):
        self.assertEqual(validate([BASE,dict(BASE,event_id="game-2")])["same_game_multi_leg_events"],0)
    def test_post_kickoff_rejected(self):
        result=validate([dict(BASE,forecast_at="2026-10-25T14:00:00-04:00")])
        self.assertEqual(result["valid_legs"],0)
    def test_duplicates_rejected(self):
        result=validate([BASE,BASE])
        self.assertEqual(result["valid_legs"],1)
        self.assertEqual(result["rejected_rows"][0]["reason"],"duplicate_forecast")
    def test_push_rejected(self):
        self.assertEqual(validate([dict(BASE,outcome=49.5)])["valid_legs"],0)
    def test_unverified_quotes_cannot_promote(self):
        result=validate([BASE],quotes=[{"odds":200}])
        self.assertFalse(result["verified_actual_sgp_bookmaker_quote"])
        self.assertFalse(result["same_game_sgp_expected_value_validated"])

if __name__ == "__main__":
    unittest.main()
