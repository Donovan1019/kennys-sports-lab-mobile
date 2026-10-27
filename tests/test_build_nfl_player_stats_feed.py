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
 def test_negative_rushing_yards_allowed(self):
  r=build([dict(BASE,rushing_yards="-7")])
  self.assertEqual(r["players"][0]["games"][0]["values"]["Rushing yards"],-7)
 def test_negative_receptions_rejected(self):
  with self.assertRaises(ValueError):build([dict(BASE,receptions="-1")])
 def test_anonymous_row_quarantined(self):
  r=build([dict(BASE,player_id="",player_display_name=""),BASE])
  self.assertEqual(r["quarantine"]["count"],1)
  self.assertEqual(r["quarantine"]["records"][0]["reason"],"missing_player_id_and_name")
  self.assertEqual(len(r["players"]),1)
 def test_partial_identity_still_rejected(self):
  with self.assertRaises(ValueError):build([dict(BASE,player_id="")])
 def test_all_anonymous_still_rejected(self):
  with self.assertRaises(ValueError):build([dict(BASE,player_id="",player_display_name="")])
 def test_punctuation_name_variant_same_id(self):
  a=dict(BASE,player_display_name="O'Neil Smith")
  b=dict(BASE,player_display_name="ONeil Smith",game_id="2026_04_A_B",week="4")
  result=build([a,b])
  self.assertEqual(len(result["players"]),1)
  self.assertEqual(len(result["players"][0]["games"]),2)
  self.assertIn("ONeil Smith",result["players"][0]["name_variants"])
 def test_distinct_name_same_id_rejected(self):
  with self.assertRaisesRegex(ValueError,"previous_name"):
   build([BASE,dict(BASE,player_display_name="Different Person",game_id="2026_04_A_B",week="4")])
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
