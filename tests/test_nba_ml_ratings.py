import unittest
from scripts.build_nba_ml_ratings import fit,predict,NBA_TEAMS,holdout_audit
class EloTests(unittest.TestCase):
 def test_probabilities(self):
  self.assertAlmostEqual(predict(0),0.5)
  self.assertGreater(predict(100),0.5)
 def test_only_nba_franchises(self):
  self.assertEqual(len(NBA_TEAMS),30)
  self.assertNotIn('Team Stars',NBA_TEAMS)
  self.assertNotIn('World',NBA_TEAMS)
 def test_fail_closed_on_insufficient_data(self):
  with self.assertRaises(ValueError):fit([])
 def test_holdout_requires_enough_games(self):
  with self.assertRaises(ValueError):holdout_audit([])
 def test_holdout_deterministic(self):
  teams=sorted(NBA_TEAMS)
  games=[{"date":f"2025-11-{(i//15)%28+1:02d}T{(i%15):02d}:00:00Z","id":str(i),
          "home":teams[i%30],"away":teams[(i+1)%30],"home_win":i%2} for i in range(600)]
  result=holdout_audit(games)
  self.assertGreaterEqual(result["games"],100)
  self.assertEqual(result,holdout_audit(list(reversed(games))))
  self.assertIn("constant_baseline_brier",result)
if __name__=="__main__":unittest.main()
