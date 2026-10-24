import unittest
from datetime import datetime,timezone,timedelta
from scripts.ufc_pit_odds_integrity import audit,implied
class OddsIntegrityTests(unittest.TestCase):
 def setUp(self):
  self.now=datetime(2026,10,24,9,tzinfo=timezone.utc)
  self.feed={"source":"test","fetched_at":"2026-10-24T08:30:00Z","odds":[
   {"event_id":"f1","bookmaker":"dk","market":"h2h","selection":"A","price":-120,"updated_at":"2026-10-24T08:20:00Z","commence_time":"2026-10-24T12:00:00Z"},
   {"event_id":"f1","bookmaker":"dk","market":"h2h","selection":"B","price":110,"updated_at":"2026-10-24T08:20:00Z","commence_time":"2026-10-24T12:00:00Z"}]}
 def test_valid_two_sided_market(self):
  r=audit(self.feed,self.now)
  self.assertEqual(r["verified_pre_fight_markets"],1)
  self.assertAlmostEqual(sum(r["markets"][0]["no_vig_probabilities"].values()),1)
 def test_stale_quote_rejected(self):
  self.feed["odds"][0]["updated_at"]="2026-10-23T01:00:00Z"
  r=audit(self.feed,self.now)
  self.assertIn("STALE_QUOTE",r["markets"][0]["issues"])
 def test_future_quote_rejected(self):
  self.feed["odds"][0]["updated_at"]="2026-10-24T10:00:00Z"
  self.assertIn("FUTURE_QUOTE_TIMESTAMP",audit(self.feed,self.now)["markets"][0]["issues"])
 def test_after_start_rejected(self):
  self.now=datetime(2026,10,24,13,tzinfo=timezone.utc)
  self.assertIn("FIGHT_STARTED",audit(self.feed,self.now)["markets"][0]["issues"])
 def test_missing_opponent_rejected(self):
  self.feed["odds"].pop()
  self.assertEqual(audit(self.feed,self.now)["verified_pre_fight_markets"],0)
 def test_american_price(self):
  self.assertAlmostEqual(implied(-150),.6)
  self.assertAlmostEqual(implied(200),1/3)
if __name__=="__main__":unittest.main()
