import unittest
from datetime import datetime,timedelta,timezone
from scripts.nfl_pregame_research import forecasts

NOW=datetime(2026,10,21,12,tzinfo=timezone.utc)
def games(count=9):
    rows=[]
    for i in range(count):
        rows.append({"date":(NOW-timedelta(days=i+1)).isoformat(),"home":"Home","away":"Away","home_score":24,"away_score":17})
    return rows
def market():
    return {"events":[{"event_id":"nfl-e","home":"Home","away":"Away","home_consensus_no_vig":.55}]}
class NflResearchTests(unittest.TestCase):
    def test_strictly_prior_day_and_research_only(self):
        result=forecasts(games(),market(),NOW)
        self.assertEqual(result["forecast_count"],1)
        self.assertFalse(result["events"][0]["bet_eligible"])
        self.assertTrue(0<result["events"][0]["model_probability"]<1)
    def test_insufficient_history_fails_closed(self):
        result=forecasts(games(7),market(),NOW)
        self.assertEqual(result["forecast_count"],0)
    def test_same_day_results_are_excluded(self):
        prior=games(7)
        prior.append({"date":(NOW-timedelta(hours=1)).isoformat(),"home":"Home","away":"Away","home_score":70,"away_score":0})
        self.assertEqual(forecasts(prior,market(),NOW)["forecast_count"],0)
if __name__=="__main__":unittest.main()
