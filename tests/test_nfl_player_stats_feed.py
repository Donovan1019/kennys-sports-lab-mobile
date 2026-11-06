import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from audit_nfl_player_stats_feed import inspect
class FeedAudit(unittest.TestCase):
    def check(self,payload):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"feed.json"
            p.write_text(json.dumps(payload))
            return inspect(p)
    def test_empty_feed_blocked(self):
        r=self.check({"source":"nflverse-stats-player-week","players":[]})
        self.assertEqual(r["status"],"BLOCKED")
    def test_missing_provenance_is_blocked(self):
        r=self.check({"source":"nflverse-stats-player-week","players":[{"player_id":"p1","games":[{"game_id":"g1","values":{"Passing yards":100}}]}]})
        self.assertEqual(r["status"],"BLOCKED")
        self.assertIn("missing_independent_source_provenance",r["issues"])
        self.assertIn("missing_verified_game_date",r["issues"])
        self.assertFalse(r["betting_eligible"])
    def test_complete_fixture_provenance_verified_but_not_bet_eligible(self):
        payload={"source":"nflverse-stats-player-week","independentlyVerified":True,
                 "fetched_at":"2026-11-06T00:00:00Z","source_note":"verified test fixture",
                 "players":[{"player_id":"p1","games":[{"game_id":"g1",
                 "game_date":"2026-11-01","verified":True,
                 "values":{"Passing yards":100}}]}]}
        r=self.check(payload)
        self.assertEqual(r["status"],"SOURCE_PROVENANCE_VERIFIED")
        self.assertFalse(r["betting_eligible"])
        self.assertEqual(r["issues"],[])
    def test_duplicate_event_blocked(self):
        game={"game_id":"g1","values":{"Passing yards":100}}
        r=self.check({"source":"nflverse-stats-player-week","players":[{"player_id":"p1","games":[game,game]}]})
        self.assertIn("duplicate_player_game_ids",r["issues"])
    def test_missing_values_blocked(self):
        r=self.check({"source":"nflverse-stats-player-week","players":[{"player_id":"p1","games":[{"game_id":"g1","values":{}}]}]})
        self.assertIn("missing_stat_values",r["issues"])
if __name__=="__main__":unittest.main()
