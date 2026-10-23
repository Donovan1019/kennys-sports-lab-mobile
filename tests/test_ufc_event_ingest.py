import datetime as dt
import unittest
from scripts.ufc_event_ingest import parse

NOW = dt.datetime(2026, 10, 23, tzinfo=dt.timezone.utc)

def bout(identifier, date, names=("Fighter A", "Fighter B")):
    return {"id": identifier, "date": date, "competitors": [{"athlete": {"displayName": name}} for name in names]}

class UFCIngestTests(unittest.TestCase):
    def test_filters_past_incomplete_and_duplicate_bouts(self):
        future = bout("1", "2026-10-24T22:00:00Z")
        past = bout("2", "2026-10-22T22:00:00Z")
        invalid = bout("3", "not-a-date")
        feed = {"events": [{"name": "UFC test", "competitions": [future, future, past, invalid, {"id": "4", "competitors": []}]}]}
        result = parse(feed, NOW)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "1")
        self.assertFalse(result[0]["bet_eligible"])
        self.assertFalse(result[0]["odds_verified"])
        self.assertIsNone(result[0]["scheduled_rounds"])
    def test_empty_feed_is_safe(self):
        self.assertEqual(parse({}, NOW), [])
    def test_ignores_naive_dates(self):
        self.assertEqual(parse({"events": [{"competitions": [bout("x", "2026-10-24T22:00:00")]}]}, NOW), [])

if __name__ == "__main__":
    unittest.main()
