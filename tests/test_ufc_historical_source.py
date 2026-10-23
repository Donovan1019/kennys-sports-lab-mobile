import datetime as dt
import unittest
from unittest.mock import patch
from scripts.ufc_historical_source import parse_day,collect
DAY=dt.date(2026,10,20)
def payload(method=None,complete=True):
    return {"events":[{"id":"event1","date":"2026-10-20T20:00:00Z","competitions":[{"id":"fight1","date":"2026-10-20T20:00:00Z",
      "status":{"type":{"completed":complete}},"verified_method":method,
      "competitors":[{"winner":True,"athlete":{"displayName":"A"}},{"winner":False,"athlete":{"displayName":"B"}}]}]}]}
class UFCHistoricalSourceTests(unittest.TestCase):
    def test_unverified_methods_not_ingested(self):
        self.assertEqual(parse_day(payload(),DAY),[])
    def test_completed_verified_bout(self):
        rows=parse_day(payload("KO/TKO"),DAY)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["winner"],"A")
    def test_incomplete_bout_excluded(self):
        self.assertEqual(parse_day(payload("Decision",False),DAY),[])
    def test_bounds_and_partial_failure(self):
        with self.assertRaises(ValueError):collect(DAY,DAY+dt.timedelta(days=32))
        with patch("scripts.ufc_historical_source.fetch_day",side_effect=OSError("network")):
            r=collect(DAY,DAY)
        self.assertEqual(r["results"],[])
        self.assertEqual(len(r["failed_days"]),1)
if __name__=="__main__":unittest.main()
