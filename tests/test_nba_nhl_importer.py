import unittest
from scripts.fetch_nba_nhl_stats import parse_summary,scalar
class ImportTests(unittest.TestCase):
 def test_nba(self):
  d={"boxscore":{"players":[{"team":{"abbreviation":"BOS"},"statistics":[{"labels":["MIN","PTS","REB","AST","3PT"],"athletes":[{"athlete":{"id":"42","displayName":"Test Player"},"stats":["32:30","24","7","5","3-8"]}]}]}]}}
  r=parse_summary(d,"nba","123","2026-10-20")
  self.assertEqual(len(r),1)
  self.assertEqual(r[0]["values"]["PRA"],36)
  self.assertEqual(r[0]["values"]["Minutes"],32.5)
  self.assertEqual(r[0]["values"]["Threes"],3)
 def test_nhl(self):
  d={"boxscore":{"players":[{"team":{"abbreviation":"BOS"},"statistics":[{"labels":["G","A","PTS","SOG"],"athletes":[{"athlete":{"id":"7","displayName":"Skater"},"stats":["1","2","3","5"]}]}]}]}}
  r=parse_summary(d,"nhl","9","2026-10-20")
  self.assertEqual(r[0]["values"]["Shots on goal"],5)
 def test_empty(self):
  self.assertEqual(parse_summary({},"nba","1","2026-10-20"),[])
 def test_scalar(self):
  self.assertIsNone(scalar("DNP"))
if __name__=="__main__":unittest.main()
