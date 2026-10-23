import datetime as dt
import unittest
from scripts.ufc_elo_card_projections import build
class TestUfcEloCard(unittest.TestCase):
 def test_pre_event_and_insufficient(self):
  rows=[]
  for i in range(10):
   rows.append({"event_date":"2025-01-%02d"%(i+1),"winner":"Alpha","loser":"Beta","source_fight_url":"fight-"+str(i),"independently_verified":False})
  snap={"snapshot":"2026-07-07","bet_eligible":False,"fight_history":{"rows":rows}}
  card={"sport":"UFC","bet_eligible":False,"fights":[{"id":"1","red":"Alpha","blue":"Beta"},{"id":"2","red":"Alpha","blue":"Unknown"}]}
  report=build(snap,card,dt.datetime(2026,10,23,tzinfo=dt.timezone.utc))
  self.assertGreater(report["projections"][0]["red_research_probability"],.5)
  self.assertIsNone(report["projections"][1]["red_research_probability"])
  self.assertFalse(report["bet_eligible"])
 def test_no_future_leakage(self):
  snap={"snapshot":"2026-07-07","bet_eligible":False,"fight_history":{"rows":[{"event_date":"2026-12-01","winner":"A","loser":"B","source_fight_url":"f","independently_verified":False}]}}
  card={"sport":"UFC","bet_eligible":False,"fights":[{"id":"1","red":"A","blue":"B"}]}
  self.assertIsNone(build(snap,card,dt.datetime(2026,10,23,tzinfo=dt.timezone.utc),min_bouts=1)["projections"][0]["red_research_probability"])
 def test_reject_bet_eligible(self):
  with self.assertRaises(ValueError):build({"snapshot":"2026-07-07","bet_eligible":True},{"sport":"UFC","bet_eligible":False})
if __name__=="__main__":unittest.main()
