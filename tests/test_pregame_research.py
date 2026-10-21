import unittest
from datetime import datetime,timezone
from scripts.pregame_research import forecasts
NOW=datetime(2026,10,21,12,tzinfo=timezone.utc)
def games():
 out=[]
 for i in range(20):
  out.append({"date":f"2026-09-{i+1:02d}","home":"Home","away":"Away","home_score":110,"away_score":100})
 return out
MARKET={"events":[{"event_id":"e","home":"Home","away":"Away","home_consensus_no_vig":.6}]}
class PregameTests(unittest.TestCase):
 def test_strict_prior_day_and_probability(self):
  r=forecasts("basketball_nba",games(),MARKET,NOW,6.5)
  self.assertEqual(r["forecast_count"],1)
  self.assertFalse(r["events"][0]["bet_eligible"])
 def test_no_future_data_leakage(self):
  future=[dict(g,date="2026-10-21") for g in games()]
  r=forecasts("basketball_nba",future,MARKET,NOW,6.5)
  self.assertEqual(r["forecast_count"],0)
 def test_missing_calibration_fails_closed(self):
  r=forecasts("basketball_nba",games(),MARKET,NOW,None)
  self.assertEqual(r["forecast_count"],0)
 def test_nhl_proxy(self):
  hockey=[dict(g,home_score=3,away_score=2) for g in games()]
  r=forecasts("icehockey_nhl",hockey,MARKET,NOW)
  self.assertEqual(r["forecast_count"],1)
  self.assertFalse(r["events"][0]["bet_eligible"])
if __name__=="__main__":unittest.main()
