import unittest
from scripts.market_quality_screen import screen
class QualityTests(unittest.TestCase):
 def event(self,n=9,spread=1.2):
  return {"event_id":"e","away":"A","home":"H","bookmaker_count":n,"home_consensus_no_vig":.6,"home_probability_range_pp":spread}
 def test_never_assert_edge(self):
  r=screen(None,{"events":[self.event()]})["events"][0]
  self.assertFalse(r["bet_eligible"])
  self.assertIsNone(r["expected_roi"])
 def test_requires_three_books(self):
  self.assertEqual(screen(None,{"events":[self.event(2)]})["events"],[])
 def test_flags_dispersion(self):
  self.assertEqual(screen(None,{"events":[self.event(spread=4)]})["events"][0]["market_quality"],"dispersed")
if __name__=="__main__":unittest.main()
