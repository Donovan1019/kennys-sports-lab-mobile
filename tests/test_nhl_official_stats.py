import unittest
from scripts.fetch_nhl_official_stats import parse_boxscore
class OfficialNHLTests(unittest.TestCase):
 def test_shots_and_points(self):
  d={"awayTeam":{"abbrev":"BOS"},"homeTeam":{"abbrev":"NYR"},"playerByGameStats":{"awayTeam":{"forwards":[{"playerId":123,"name":{"default":"Test Skater"},"goals":1,"assists":2,"sog":5}],"goalies":[{"playerId":777,"name":{"default":"Test Goalie"},"saves":31}]},"homeTeam":{"defense":[{"playerId":888,"name":{"default":"Test Defender"},"goals":0,"assists":1,"sog":3}]}}}
  rows=parse_boxscore(d,"1","2026-10-20")
  self.assertEqual(len(rows),3)
  skater=next(x for x in rows if x["id"]=="123")
  self.assertEqual(skater["values"]["Shots on goal"],5)
  self.assertEqual(skater["values"]["Points"],3)
  self.assertEqual(skater["home_away"],"away")
  self.assertEqual(next(x for x in rows if x["id"]=="777")["values"]["Saves"],31)
 def test_quarantine_impossible_sog(self):
  d={"awayTeam":{"abbrev":"VGK"},"playerByGameStats":{"awayTeam":{"forwards":[{"playerId":999,"name":{"default":"Sample"},"goals":1,"assists":0,"sog":0}]}}}
  row=parse_boxscore(d,"2026020134","2026-10-17")[0]
  self.assertEqual(row["values"]["Goals"],1)
  self.assertEqual(row["values"]["Points"],1)
  self.assertNotIn("Shots on goal",row["values"])
  self.assertIn("sog_below_goals",row["quality_flags"])
 def test_extended_markets(self):
  d={"awayTeam":{"abbrev":"BOS"},"playerByGameStats":{"awayTeam":{"forwards":[{"playerId":9,"name":{"default":"Example"},"goals":2,"assists":1,"sog":5,"blockedShots":3,"hits":2,"powerPlayGoals":1,"powerPlayPoints":2}]}}}
  v=parse_boxscore(d,"1","2026-10-20")[0]["values"]
  self.assertEqual(v["Anytime goal"],1)
  self.assertEqual(v["Multi-point game"],1)
  self.assertEqual(v["Blocked shots"],3)
  self.assertEqual(v["Power-play goals"],1)
 def test_no_fabricated_values(self):
  self.assertEqual(parse_boxscore({"playerByGameStats":{}},"1","2026-10-20"),[])
if __name__=="__main__":unittest.main()
