import unittest
from scripts.betting_market_math import american_to_decimal,implied_probability,no_vig_two_way,expected_roi,fractional_kelly

class BettingMathTests(unittest.TestCase):
    def test_decimal(self):
        self.assertAlmostEqual(american_to_decimal(-110),1+100/110)
        self.assertEqual(american_to_decimal(150),2.5)
    def test_no_vig(self):
        a,b=no_vig_two_way(-110,-110)
        self.assertAlmostEqual(a,.5)
        self.assertAlmostEqual(a+b,1)
    def test_ev(self):
        self.assertAlmostEqual(expected_roi(.5,100),0)
        self.assertLess(expected_roi(.5,-110),0)
    def test_kelly(self):
        self.assertEqual(fractional_kelly(.4,-110),0)
        self.assertLessEqual(fractional_kelly(.8,100),.01)
    def test_invalid(self):
        with self.assertRaises(ValueError):implied_probability(0)
        with self.assertRaises(ValueError):expected_roi(1.2,100)

if __name__=='__main__':unittest.main()
