import datetime as dt
import unittest
from scripts.ufc_historical_backfill import backfill
DAY=dt.date(2026,10,20)
def response(day):
    return {"events":[{"id":"ev1","date":"2026-10-20T20:00:00Z","competitions":[{
        "id":"f1","date":"2026-10-20T20:00:00Z","status":{"type":{"completed":True}},
        "competitors":[{"winner":True,"athlete":{"displayName":"A"}},
                       {"winner":False,"athlete":{"displayName":"B"}}]}]}]}
class UFCBackfillTests(unittest.TestCase):
    def test_verified_winner_without_method(self):
        r=backfill(DAY,DAY,fetcher=response)
        self.assertEqual(r["verified_fights"],1)
        self.assertIsNone(r["results"][0]["method"])
        self.assertFalse(r["bet_eligible"])
    def test_resume_does_not_repeat_completed_days(self):
        r=backfill(DAY,DAY,fetcher=response)
        def fail(day):raise AssertionError("Repeated fetch")
        again=backfill(DAY,DAY,existing=r,fetcher=fail)
        self.assertEqual(again["newly_queried_days"],0)
        self.assertEqual(again["verified_fights"],1)
    def test_failed_day_retried(self):
        def fail(day):raise OSError("temporary")
        r=backfill(DAY,DAY,fetcher=fail)
        self.assertEqual(r["successful_days"],[])
        self.assertEqual(len(r["failed_days"]),1)
        retry=backfill(DAY,DAY,existing=r,fetcher=response)
        self.assertEqual(retry["verified_fights"],1)
    def test_unexpected_response_not_marked_success(self):
        r=backfill(DAY,DAY,fetcher=lambda d:{})
        self.assertEqual(r["successful_days"],[])
if __name__=="__main__":unittest.main()
