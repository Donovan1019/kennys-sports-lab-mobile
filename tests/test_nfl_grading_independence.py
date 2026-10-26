import unittest
from scripts.report_nfl_pregame_ledger import dashboard
from scripts.diagnose_nfl_rush_grading import diagnose
def f(book,id):
 return {"forecast_id":id,"event_id":"g","player":"P","market":"player_rush_yds","line":50.5,"model_probability":0.6,"over_odds":-110,"under_odds":-110,"quoted_at":"2026-10-25T12:00:00Z","forecast_at":"2026-10-25T12:01:00Z","kickoff":"2026-10-25T17:00:00Z","bookmaker":book,"model_version":"v1","source_commit":"abc","research_only":True}
def o():
 return {"event_id":"g","player":"P","market":"player_rush_yds","outcome":40,"kickoff":"2026-10-25T17:00:00Z","verified_at":"2026-10-25T21:00:00Z","outcome_verified":True,"espn_event_id":"123","source":"https://espn.com/123"}
class IndependenceTests(unittest.TestCase):
 def test_two_books_one_outcome(self):
  data={"forecasts":[f("draftkings","a"),f("fanduel","b")]}
  d=dashboard(data,[o()])
  self.assertEqual(d["markets"]["player_rush_yds"]["graded_over_forecasts"],2)
  self.assertEqual(d["markets"]["player_rush_yds"]["unique_player_game_outcomes"],1)
  self.assertEqual(d["unique_games_with_results"],1)
  r=diagnose(data,[o()])
  self.assertEqual(r["duplicate_bookmaker_exposure"],1)
if __name__=="__main__":unittest.main()
