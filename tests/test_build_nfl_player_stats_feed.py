import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from build_nfl_player_stats_feed import build,schedule_index
BASE={"season":"2026","season_type":"REG","week":"3","player_id":"p1","player_display_name":"Player One","game_id":"2026_03_A_B","passing_yards":"203","rushing_yards":"0"}
class Ingestion(unittest.TestCase):
 def test_schedule_join(self):
  row=dict(BASE,game_id="",recent_team="NYJ")
  schedule=schedule_index([{"season":"2026","week":"3","game_id":"2026_03_NYJ_BUF","home_team":"NYJ","away_team":"BUF"}])
  self.assertEqual(build([row],schedule)["players"][0]["games"][0]["game_id"],"2026_03_NYJ_BUF")
 def test_missing_schedule_match_rejected(self):
  with self.assertRaises(ValueError):build([dict(BASE,game_id="",recent_team="NYJ")],{})
 def test_observed_game(self):
  r=build([BASE])
  self.assertEqual(r["players"][0]["games"][0]["values"]["Passing yards"],203)
 def test_missing_event_rejected(self):
  with self.assertRaises(ValueError):build([dict(BASE,game_id="")])
 def test_duplicate_rejected(self):
  with self.assertRaises(ValueError):build([BASE,BASE])
 def test_no_games_rejected(self):
  with self.assertRaises(ValueError):build([])
 def test_no_missing_stats_coercion(self):
  r=build([dict(BASE,passing_yards="",rushing_yards="2")])
  self.assertNotIn("Passing yards",r["players"][0]["games"][0]["values"])
if __name__=="__main__":unittest.main()
