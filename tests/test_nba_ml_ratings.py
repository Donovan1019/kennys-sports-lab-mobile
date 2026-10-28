import unittest
from scripts.build_nba_ml_ratings import fit,predict,NBA_TEAMS
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
if __name__=="__main__":unittest.main()
