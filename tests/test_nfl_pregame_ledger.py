import unittest
from scripts.validate_nfl_pregame_ledger import validate

def sample():
    return {"snapshot_id":"s1","game_id":"g1","player_id":"p1","market":"player_rush_yds","side":"over",
            "line":55.5,"decimal_odds":1.91,"probability":0.58,
            "captured_at":"2026-10-25T16:00:00Z","kickoff_at":"2026-10-25T17:00:00Z",
            "source":"recorded-sportsbook-snapshot","model_version":"frozen-1"}

class PregameLedgerTests(unittest.TestCase):
    def test_valid_structure_still_blocked_for_betting(self):
        r=validate([sample()])
        self.assertEqual(r["status"],"VALID")
        self.assertEqual(r["bet_eligibility"],"BLOCKED")
    def test_no_backfilled_snapshots(self):
        s=sample();s["captured_at"]=s["kickoff_at"]
        self.assertEqual(validate([s])["status"],"BLOCKED")
    def test_reject_duplicates(self):
        s=sample()
        self.assertEqual(validate([s,s])["status"],"BLOCKED")
    def test_reject_missing_or_invalid_odds(self):
        s=sample();s["decimal_odds"]=float("nan")
        self.assertEqual(validate([s])["status"],"BLOCKED")
        del s["decimal_odds"]
        self.assertEqual(validate([s])["status"],"BLOCKED")
    def test_empty_is_blocked(self):
        self.assertEqual(validate([])["status"],"BLOCKED")
    def test_utc_required(self):
        s=sample();s["captured_at"]="2026-10-25T16:00:00"
        self.assertEqual(validate([s])["status"],"BLOCKED")

if __name__=="__main__": unittest.main()
