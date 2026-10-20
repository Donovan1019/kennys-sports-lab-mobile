import unittest
from scripts.connect_nfl_team_scores import parse_scoreboard,team_parameters,assemble
class TeamScoreTests(unittest.TestCase):
 def test_completed_only(self):
  def event(completed):
   return {'date':'2026-10-01T00:00:00Z','competitions':[{'status':{'type':{'completed':completed}},'competitors':[{'homeAway':'away','score':'21','team':{'displayName':'A'}},{'homeAway':'home','score':'24','team':{'displayName':'B'}}]}]}
  rows=parse_scoreboard({'events':[event(True),event(False)]})
  self.assertEqual(len(rows),1)
 def test_requires_eight_past_games(self):
  self.assertIsNone(team_parameters([],'A','2026-10-20T00:00:00+00:00'))
 def test_no_eligible_matchups(self):
  result=assemble([],{'odds':[{'sport':'americanfootball_nfl','event_id':'123','event':'A @ B'}]},'2026-10-20T00:00:00+00:00')
  self.assertEqual(result['games'],[])
if __name__=='__main__':unittest.main()
