import unittest
from datetime import datetime, timezone, timedelta
from scripts.nba_research_candidates import generate

NOW=datetime(2026,10,28,12,0,tzinfo=timezone.utc)
def source():
    odds={"sport":"basketball_nba","fetched_at":(NOW-timedelta(minutes=2)).isoformat(),
          "odds":[{"event_id":"game","event":"A @ B","commence_time":(NOW+timedelta(hours=6)).isoformat(),
          "updated_at":(NOW-timedelta(minutes=3)).isoformat(),"player":"Example Player",
          "market":"player_points","selection":"Over","point":19.5,"price":-110,"bookmaker":"fanduel"}]}
    history={"sport":"nba","source":"espn-public-boxscore","players":[{"name":"Example Player","team":"A",
             "games":[{"date":(NOW-timedelta(days=i)).strftime("%Y-%m-%d"),"values":{"Points":22}} for i in range(1,11)]}]}
    return odds,history

class CandidateTests(unittest.TestCase):
    def test_history_is_research_only(self):
        result=generate(*source(),NOW)
        self.assertEqual(len(result["predictions"]),1)
        p=result["predictions"][0]
        self.assertEqual(p["historical_hits"],10)
        self.assertIsNone(p["model_probability"])
        self.assertIsNone(p["sgp_joint_probability"])
        self.assertFalse(p["bet_eligible"])
    def test_stale_feed_blocked(self):
        odds,history=source()
        odds["fetched_at"]=(NOW-timedelta(hours=2)).isoformat()
        self.assertEqual(generate(odds,history,NOW)["predictions"],[])
    def test_post_tipoff_blocked(self):
        odds,history=source()
        odds["odds"][0]["commence_time"]=(NOW-timedelta(minutes=1)).isoformat()
        self.assertEqual(generate(odds,history,NOW)["predictions"],[])
    def test_player_from_other_team_blocked(self):
        odds,history=source()
        history["players"][0]["team"]="Other Team"
        result=generate(odds,history,NOW)
        self.assertEqual(result["predictions"],[])
        self.assertEqual(result["rejections"]["player_team_mismatch"],1)
    def test_missing_team_blocked(self):
        odds,history=source()
        del history["players"][0]["team"]
        self.assertEqual(generate(odds,history,NOW)["predictions"],[])
    def test_unknown_player_blocked(self):
        odds,history=source()
        odds["odds"][0]["player"]="Unknown Player"
        self.assertEqual(generate(odds,history,NOW)["predictions"],[])

if __name__=="__main__":unittest.main()
