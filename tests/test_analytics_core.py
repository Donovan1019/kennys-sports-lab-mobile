import unittest
from scripts.analytics_core import analyze,american_break_even,no_vig_two_way
class AnalyticsTests(unittest.TestCase):
 def test_rate_and_bounds(self):
  a=analyze([10,20,30,40],20,trials=10000)
  self.assertEqual(a["hits"],3)
  self.assertEqual(a["historical_rate"],.75)
  self.assertLessEqual(a["wilson_95"][0],.75)
  self.assertGreaterEqual(a["wilson_95"][1],.75)
  self.assertFalse(a["is_forecast"])
 def test_seed(self):
  self.assertEqual(analyze([0,1,2],1),analyze([0,1,2],1))
 def test_strict_over(self):
  self.assertEqual(analyze([1,2,3],2,inclusive=False)["hits"],1)
 def test_invalid(self):
  for v in ([],[float("nan")],[float("inf")],[-1]):
   with self.assertRaises(ValueError):analyze(v,1)
 def test_prices(self):
  self.assertAlmostEqual(american_break_even(-110),110/210)
  self.assertAlmostEqual(american_break_even(150),.4)
  a,b=no_vig_two_way(-110,-110)
  self.assertAlmostEqual(a+b,1)
 def test_price_invalid(self):
  with self.assertRaises(ValueError):american_break_even(0)
if __name__=="__main__":unittest.main()
