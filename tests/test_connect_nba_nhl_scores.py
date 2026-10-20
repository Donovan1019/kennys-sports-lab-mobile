import unittest
from scripts.connect_nba_nhl_scores import parse_league,build_inputs
class LeagueTests(unittest.TestCase):
 def test_regular_season_only(self):
  def event(kind):
   return {"season":{"type":kind},"date":"2026-10-01T00:00:00Z","competitions":[{"status":{"type":{"completed":True}},"competitors":[{"homeAway":"away","score":"101","team":{"displayName":"A"}},{"homeAway":"home","score":"99","team":{"displayName":"B"}}]}]}
  self.assertEqual(len(parse_league({"events":[event(1),event(2),event(3)]})),1)
  self.assertEqual(len(parse_league({"events":[event("2")]})),1)
 def test_missing_odds_produces_no_events(self):
  self.assertEqual(build_inputs([],{"odds":[]},"basketball_nba","2026-10-20T00:00:00+00:00")["games"],[])
if __name__=="__main__":unittest.main()
