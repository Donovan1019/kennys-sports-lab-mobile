import unittest
from scripts.ufc_dk_fd_compare import compare

def snapshot(book):
    return {"schema":1,"sport":"UFC","source":book,"source_authorized":True,
            "captured_at_utc":"2026-10-23T12:00:00Z",
            "moneylines":[{"event_id":"event1","fighter":"A","opponent":"B",
                "fighter_odds":-110,"opponent_odds":-110,"event_start_utc":"2026-10-24T12:00:00Z",
                "sportsbook":book,"model_probability":0.58}]}

class ProviderTests(unittest.TestCase):
    def test_two_providers(self):
        r=compare({"draftkings":snapshot("DraftKings"),"fanduel":snapshot("FanDuel")})
        self.assertEqual(r["comparisons"][0]["status"],"COMPARABLE_RESEARCH")
        self.assertFalse(r["bet_eligible"])
    def test_missing_feed(self):
        r=compare({"draftkings":snapshot("DraftKings")})
        self.assertEqual(r["providers"]["fanduel"]["status"],"MISSING_FEED")
    def test_no_fake_odds(self):
        r=compare({"draftkings":snapshot("DraftKings"),"fanduel":snapshot("FanDuel")})
        self.assertFalse(r["comparisons"][0]["bet_eligible"])
if __name__=="__main__": unittest.main()
