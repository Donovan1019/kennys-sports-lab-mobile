import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from nfl_sgp_joint_evidence import validate

BASE = dict(event_id="game-1", player_id="p1", market="receiving_yards",
            line=49.5, side="over", forecast_at="2026-10-25T12:00:00-04:00",
            kickoff_at="2026-10-25T13:00:00-04:00", outcome=65, probability=.65)

class TestSGPJointEvidence(unittest.TestCase):
    def test_same_game_and_baseline(self):
        b = dict(BASE, player_id="p2", probability=.7, outcome=35)
        result = validate([BASE,b])
        self.assertEqual(result["same_game_multi_leg_events"],1)
        self.assertAlmostEqual(result["independent_joint_baseline_brier"], (.65*.7)**2)
        self.assertFalse(result["betting_eligible"])
        self.assertIsNone(result["joint_model_brier"])
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
