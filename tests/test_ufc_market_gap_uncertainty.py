import unittest
from scripts.ufc_market_gap_uncertainty import cluster_bootstrap

class MarketUncertaintyTests(unittest.TestCase):
 def test_market_dominates_every_event(self):
  rows=[(.5,.9,1,"2025-01-01"),(.5,.1,0,"2025-02-01"),
        (.5,.9,1,"2025-03-01"),(.5,.1,0,"2025-04-01")]
  result=cluster_bootstrap(rows,iterations=200)
  self.assertTrue(result["market_advantage_significant_95pct"])
  self.assertGreater(result["bootstrap_95_low"],0)
 def test_model_dominates_every_event(self):
  rows=[(.9,.5,1,"2025-01-01"),(.1,.5,0,"2025-02-01")]
  result=cluster_bootstrap(rows,iterations=200)
  self.assertTrue(result["model_advantage_significant_95pct"])
 def test_deterministic(self):
  rows=[(.5,.6,1,"2025-01-01"),(.5,.4,0,"2025-02-01")]
  self.assertEqual(cluster_bootstrap(rows,iterations=100),cluster_bootstrap(rows,iterations=100))
 def test_single_date_not_certified(self):
  with self.assertRaises(ValueError):cluster_bootstrap([(.5,.6,1,"2025-01-01")])
if __name__=="__main__":unittest.main()
