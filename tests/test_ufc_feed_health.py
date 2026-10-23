import unittest
from scripts.ufc_feed_health import summarize

class FeedHealthTests(unittest.TestCase):
    def test_missing_both(self):
        r=summarize({"providers":{},"comparisons":[]},"2026-10-23T14:00:00Z")
        self.assertEqual(r["providers"]["draftkings"]["status"],"MISSING_FEED")
        self.assertFalse(r["live_connected"])
        self.assertFalse(r["bet_eligible"])
    def test_stale_provider(self):
        r=summarize({"providers":{"draftkings":{"status":"IMPORTED",
          "captured_at_utc":"2026-10-23T13:00:00Z","markets":[{"eligible":False}]}}},
          "2026-10-23T14:00:00Z")
        self.assertEqual(r["providers"]["draftkings"]["status"],"STALE_FEED")
    def test_research_only_with_recent_quotes(self):
        f={"status":"IMPORTED","captured_at_utc":"2026-10-23T13:59:00Z","markets":[{"eligible":False}]}
        r=summarize({"providers":{"draftkings":f,"fanduel":f},"comparisons":[]},
                    "2026-10-23T14:00:00Z")
        self.assertTrue(r["comparison_ready_for_research"])
        self.assertFalse(r["bet_eligible"])
    def test_future_timestamp_rejected(self):
        f={"status":"IMPORTED","captured_at_utc":"2026-10-23T15:00:00Z","markets":[{}]}
        r=summarize({"providers":{"fanduel":f}},"2026-10-23T14:00:00Z")
        self.assertEqual(r["providers"]["fanduel"]["status"],"FUTURE_TIMESTAMP")
if __name__=="__main__": unittest.main()
