import unittest
from datetime import datetime,timezone,timedelta
from scripts.collect_the_odds_api import normalize
from scripts.paired_moneyline_market import paired_moneylines
NOW=datetime(2026,10,21,12,tzinfo=timezone.utc)
class AdapterTests(unittest.TestCase):
 def event(self):
  return {"id":"id","home_team":"Home","away_team":"Away","commence_time":(NOW+timedelta(hours=2)).isoformat(),"bookmakers":[{"key":"book","markets":[{"key":"h2h","last_update":(NOW-timedelta(minutes=2)).isoformat(),"outcomes":[{"name":"Away","price":110},{"name":"Home","price":-130}]}]}]}
 def test_valid_pair(self):
  f=normalize("basketball_nba",[self.event()])
  self.assertEqual(len(f["odds"]),2)
  self.assertEqual(len(paired_moneylines(f,NOW)),1)
 def test_missing_side(self):
  e=self.event();e["bookmakers"][0]["markets"][0]["outcomes"].pop()
  self.assertEqual(len(paired_moneylines(normalize("basketball_nba",[e]),NOW)),0)
 def test_wrong_market(self):
  e=self.event();e["bookmakers"][0]["markets"][0]["key"]="spreads"
  self.assertEqual(normalize("basketball_nba",[e])["odds"],[])
if __name__=="__main__":unittest.main()
