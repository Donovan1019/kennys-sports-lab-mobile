import copy
import unittest
from scripts.ufc_style_matchup import matchup
def fighter(name):
    return {"name":name,"stats_verified":True,"observed_minutes":90,
            "sig_strikes_landed_per_min":4.5,"sig_strikes_absorbed_per_min":3.2,
            "sig_strike_accuracy":.48,"sig_strike_defense":.57,
            "takedowns_per_15":2.0,"takedown_accuracy":.42,
            "takedown_defense":.7,"submission_attempts_per_15":.8}
class UFCStyleMatchupTests(unittest.TestCase):
    def test_matchup_diagnostics_no_fake_probability(self):
        r=matchup(fighter("A"),fighter("B"))
        self.assertAlmostEqual(r["red_indicators"]["striking_volume_differential_per_min"],1.3)
        self.assertIsNone(r["winner_probability"])
        self.assertFalse(r["bet_eligible"])
    def test_missing_stats_blocked(self):
        bad=fighter("A");bad["stats_verified"]=False
        with self.assertRaises(ValueError):matchup(bad,fighter("B"))
    def test_insufficient_time_blocked(self):
        bad=fighter("A");bad["observed_minutes"]=5
        with self.assertRaises(ValueError):matchup(bad,fighter("B"))
    def test_invalid_percent_blocked(self):
        bad=fighter("A");bad["takedown_defense"]=70
        with self.assertRaises(ValueError):matchup(bad,fighter("B"))
if __name__=="__main__":unittest.main()
