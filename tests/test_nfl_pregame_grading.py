import unittest
from scripts.grade_nfl_pregame_ledger import grade

def snapshot():
    return {"snapshot_id":"x","game_id":"g","player_id":"p","market":"player_rush_yds","side":"over","line":50.5,"decimal_odds":1.9,"probability":0.6,"captured_at":"2026-10-25T12:00:00Z","kickoff_at":"2026-10-25T17:00:00Z","source":"book","model_version":"frozen"}

class GradeLedgerTests(unittest.TestCase):
    def test_win(self):
        r=grade([snapshot()],[{"game_id":"g","player_id":"p","market":"player_rush_yds","actual":60,"final_at":"2026-10-25T21:00:00Z"}])
        self.assertEqual(r["results"][0]["outcome"],"win")
        self.assertEqual(r["net_units"],0.9)
        self.assertEqual(r["bet_eligibility"],"BLOCKED")
    def test_pending(self):
        self.assertEqual(grade([snapshot()],[])["pending"],1)
    def test_post_kickoff_snapshot_blocked(self):
        s=snapshot();s["captured_at"]=s["kickoff_at"]
        self.assertEqual(grade([s],[])["status"],"BLOCKED")
    def test_early_result_rejected(self):
        with self.assertRaises(ValueError):
            grade([snapshot()],[{"game_id":"g","player_id":"p","market":"player_rush_yds","actual":60,"final_at":"2026-10-25T16:00:00Z"}])

if __name__=="__main__":unittest.main()
