import datetime as dt
import unittest
from scripts.validate_nfl_wr_betting import validate, process

class BettingFeedTests(unittest.TestCase):
    def setUp(self):
        self.now = dt.datetime(2026, 11, 12, 20, 0, tzinfo=dt.timezone.utc)
        self.pick = dict(player_name="Test Receiver", team="BUF", market="receptions", side="over",
            book="Testbook", line=4.5, american_odds=-110, model_probability=.60,
            simulations=10000, verified_at="2026-11-12T19:55:00Z", injury_verified=True,
            game_status_verified=True, projection_source="independent-model-v1",
            simulation_source="mc-v1")
    def test_complete_pick(self):
        self.assertEqual(validate(self.pick, self.now), (True, "verified"))
    def test_reject_stale(self):
        self.pick["verified_at"] = "2026-11-12T19:00:00Z"
        self.assertFalse(validate(self.pick, self.now)[0])
    def test_reject_missing_injury(self):
        self.pick["injury_verified"] = False
        self.assertFalse(validate(self.pick, self.now)[0])
    def test_reject_missing_simulations(self):
        self.pick["simulations"] = 100
        self.assertFalse(validate(self.pick, self.now)[0])
    def test_ev_math(self):
        p = process({"picks":[self.pick]}, self.now)["picks"][0]
        self.assertAlmostEqual(p["expected_value_per_unit"], .6 * (100 / 110) - .4)
        self.assertEqual(p["status"], "BETTING_READY")

if __name__ == "__main__":
    unittest.main()
