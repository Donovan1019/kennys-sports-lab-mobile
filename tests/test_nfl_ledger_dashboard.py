import unittest
from scripts.bridge_nfl_existing_prop_feeds import bridge
from scripts.report_nfl_pregame_ledger import dashboard

def forecast():
 return {"forecast_id":"a","event_id":"g","player":"P","market":"player_rush_yds","line":50.5,"model_probability":0.6,"over_odds":-110,"under_odds":-110,"quoted_at":"2026-10-25T12:00:00Z","forecast_at":"2026-10-25T12:01:00Z","kickoff":"2026-10-25T17:00:00Z","bookmaker":"draftkings","model_version":"v1","source_commit":"abc","research_only":True}
def result():
 return {"event_id":"g","player":"P","market":"player_rush_yds","outcome":60,"kickoff":"2026-10-25T17:00:00Z","verified_at":"2026-10-25T21:00:00Z","outcome_verified":True,"espn_event_id":"123","source":"https://espn.com/123"}
class DashboardTests(unittest.TestCase):
 def test_market_summary_counts_only_over(self):
  d=dashboard({"forecasts":[forecast()]},[result()])
  self.assertEqual(d["markets"]["player_rush_yds"]["graded_over_forecasts"],1)
  self.assertEqual(d["total_graded_sides"],2)
  self.assertEqual(d["bet_eligibility"],"BLOCKED")
 def test_unsupported_market_disclosed(self):
  x=forecast();x["forecast_id"]="b";x["market"]="player_pass_tds"
  d=dashboard({"forecasts":[forecast(),x]},[result()])
  self.assertEqual(d["coverage"]["excluded_unsupported_market_forecasts"],1)
 def test_invalid_timestamps_fail_closed(self):
  x=forecast();x["forecast_at"]="2026-10-25T19:00:00Z"
  self.assertEqual(dashboard({"forecasts":[x]},[result()])["status"],"BLOCKED")
if __name__=="__main__":unittest.main()
