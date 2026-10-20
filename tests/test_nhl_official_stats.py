import unittest
from scripts.fetch_nhl_official_stats import parse_boxscore
class OfficialNHLTests(unittest.TestCase):
 def test_shots_and_points(self):
  d={"awayTeam":{"abbrev":"BOS"},"homeTeam":{"abbrev":"NYR"},"playerByGameStats":{"awayTeam":{"forwards":[{"playerId":123,"name":{"default":"Test Skater"},"goals":1,"assists":2,"shots":5}],"goalies":[{"playerId":777,"name":{"default":"Test Goalie"},"saves":31}]},"homeTeam":{"defense":[{"playerId":888,"name":{"default":"Test Defender"},"goals":0,"assists":1,"shots":3}]}}}
  rows=parse_boxscore(d,"1","2026-10-20")
  self.assertEqual(len(rows),3)
  skater=next(x for x in rows if x["id"]=="123")
  self.assertEqual(skater["values"]["Shots on goal"],5)
  self.assertEqual(skater["values"]["Points"],3)
  self.assertEqual(skater["home_away"],"away")
  self.assertEqual(next(x for x in rows if x["id"]=="777")["values"]["Saves"],31)
 def test_no_fabricated_values(self):
  self.assertEqual(parse_boxscore({"playerByGameStats":{}},"1","2026-10-20"),[])
if __name__=="__main__":unittest.main()
