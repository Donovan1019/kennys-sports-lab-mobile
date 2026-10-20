import unittest
from scripts.backtest_nfl import evaluate
class BacktestTests(unittest.TestCase):
 def test_no_data_no_pass(self):
  r=evaluate([],trials=1000)
  self.assertFalse(r["passed"])
  self.assertEqual(r["sample_size"],0)
 def test_future_games_not_used(self):
  games=[{"date":"2026-01-01T00:00:00+00:00","away":"A","home":"B","away_score":20,"home_score":23}]
  r=evaluate(games,trials=1000)
  self.assertEqual(r["sample_size"],0)
 def test_no_false_pass_on_small_sample(self):
  games=[]
  for i in range(10):
   games.append({"date":f"2026-01-{i+1:02d}T00:00:00+00:00","away":"A","home":"B","away_score":20+i,"home_score":23+i})
  r=evaluate(games,trials=1000)
  self.assertFalse(r["passed"])
if __name__=="__main__":unittest.main()
