import datetime as dt
import unittest
from scripts.simulate_nba_ml_possessions import metrics, simulate
NOW=dt.datetime(2026,10,30,tzinfo=dt.timezone.utc)
class TestPossessions(unittest.TestCase):
 def test_no_evidence_fails_closed(self):
  self.assertEqual(simulate("Boston Celtics","Miami Heat",{},"test")["status"],"unavailable")
 def test_historical_boxscores_required(self):
  games=[{"date":"2026-10-01T00:00:00Z","home":"Boston Celtics","away":"Miami Heat","box":{"Boston Celtics":{"fga":90,"orb":10,"turnovers":12,"fta":20,"points":110},"Miami Heat":{"fga":90,"orb":10,"turnovers":12,"fta":20,"points":100}}}]
  self.assertEqual(metrics(games,NOW),{})
 def test_deterministic_possession_simulation(self):
  data={"Boston Celtics":{"pace":99,"offense_ppp":1.15,"defense_ppp_allowed":1.07},"Miami Heat":{"pace":97,"offense_ppp":1.10,"defense_ppp_allowed":1.12}}
  a=simulate("Boston Celtics","Miami Heat",data,"event",100)
  self.assertEqual(a,simulate("Boston Celtics","Miami Heat",data,"event",100))
  self.assertFalse(a["betting_eligible"])
  self.assertEqual(a["status"],"diagnostic_only")
if __name__=="__main__":unittest.main()
