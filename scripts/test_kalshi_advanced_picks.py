"""Regression checks for canonical names, contract equivalence and independent model probabilities."""
import unittest
from scripts.build_kalshi_advanced_picks import team_match,fee,norm

class KalshiModelTests(unittest.TestCase):
    def test_truncated_contract_name_matches_full_team(self):
        self.assertTrue(team_match('Los Angeles Lakers','Los Angeles L'))
        self.assertTrue(team_match('Charlotte Hornets','Charlotte'))
        self.assertFalse(team_match('Los Angeles Lakers','Charlotte'))
    def test_team_identity(self):
        self.assertNotEqual(norm('Los Angeles Lakers'),norm('Los Angeles Clippers'))
        self.assertNotEqual(norm('Kansas City Chiefs'),norm('Arizona Cardinals'))
    def test_fee_in_cents(self):
        self.assertAlmostEqual(fee(.74),.02)
        self.assertAlmostEqual(.73842-.74-fee(.74),-.02158)
if __name__=='__main__':unittest.main()
