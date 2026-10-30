import unittest
from scripts.fetch_nba_ml_possession_boxscores import extract
GAME={"id":"123","date":"2026-10-20T00:00:00Z","home":"Boston Celtics","away":"Miami Heat"}
def side(name):
 return {"team":{"displayName":name},"statistics":[{"name":"fieldGoalsMade-fieldGoalsAttempted","displayValue":"40-90"},{"name":"freeThrowsMade-freeThrowsAttempted","displayValue":"15-20"},{"name":"offensiveRebounds","displayValue":"10"},{"name":"turnovers","displayValue":"12"}]}
def summary():
 return {"boxscore":{"teams":[side("Boston Celtics"),side("Miami Heat")]},"header":{"competitions":[{"competitors":[{"team":{"displayName":"Boston Celtics"},"score":"105"},{"team":{"displayName":"Miami Heat"},"score":"100"}]}]}}
class TestESPNBoxscores(unittest.TestCase):
 def test_team_totals(self):
  result=extract(summary(),GAME)
  self.assertEqual(result["box"]["Boston Celtics"]["fga"],90)
  self.assertEqual(result["box"]["Miami Heat"]["fta"],20)
 def test_missing_turnovers_rejected(self):
  s=summary();s["boxscore"]["teams"][0]["statistics"].pop()
  self.assertIsNone(extract(s,GAME))
if __name__=="__main__":unittest.main()
