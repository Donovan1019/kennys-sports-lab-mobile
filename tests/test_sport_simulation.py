import unittest
from scripts.sport_simulation import simulate_sport
from scripts.market_backtest import summarize
class SportSimulationTests(unittest.TestCase):
 def test_nhl_no_ties(self):
  a=simulate_sport("icehockey_nhl",3,3,1,1,trials=1000,seed=3)
  self.assertEqual(len(a),1000)
  self.assertTrue(all(x!=y for x,y in a))
  self.assertTrue(all(isinstance(x,int) and isinstance(y,int) for x,y in a))
 def test_nhl_reproducible(self):
  self.assertEqual(simulate_sport("icehockey_nhl",2,3,1,1,trials=1000,seed=7),simulate_sport("icehockey_nhl",2,3,1,1,trials=1000,seed=7))
 def test_invalid_nhl(self):
  with self.assertRaises(ValueError):simulate_sport("icehockey_nhl",-1,3,1,1,trials=1000)
 def test_no_market_lines(self):
  r=summarize({"results":[{"home_projected_points":100,"away_projected_points":90,"actual_home_points":101,"actual_away_points":95}]})
  self.assertEqual(r["ats_backtest"],"UNAVAILABLE_NO_HISTORICAL_MARKET_LINES")
  self.assertEqual(r["margin"]["mae"],4)
if __name__=="__main__":unittest.main()
