import unittest
from scripts.simulate_nba_ml_possessions import simulate
class TestNbaOvertime(unittest.TestCase):
 def test_full_game_probability_and_overtime(self):
  d={"A":{"pace":100,"offense_ppp":1.1,"defense_ppp_allowed":1.1},"B":{"pace":100,"offense_ppp":1.1,"defense_ppp_allowed":1.1}}
  r=simulate("A","B",d,"overtime-test",draws=1000)
  self.assertEqual(r["status"],"diagnostic_only")
  self.assertFalse(r["overtime_unmodeled"])
  self.assertGreater(r["overtime_periods_simulated"],0)
  self.assertTrue(0<=r["home_full_game_win_probability"]<=1)
  self.assertFalse(r["betting_eligible"])
if __name__=="__main__":unittest.main()
