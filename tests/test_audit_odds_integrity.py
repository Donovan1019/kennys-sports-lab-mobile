import unittest
from datetime import datetime,timezone,timedelta
from scripts.audit_odds_integrity import audit
NOW=datetime(2026,10,20,22,tzinfo=timezone.utc)
def row(start,updated,price=-110):
    return {"event_id":"game1","selection":"Home","bookmaker":"book","price":price,"commence_time":start.isoformat(),"updated_at":updated.isoformat()}
class OddsAuditTests(unittest.TestCase):
    def test_pregame_fresh(self):
        a=audit({"odds":[row(NOW+timedelta(hours=2),NOW-timedelta(minutes=5))]},NOW)
        self.assertEqual(a["eligible_events"],1)
        self.assertFalse(a["betting_ready"])
    def test_live_excluded(self):
        a=audit({"odds":[row(NOW-timedelta(minutes=1),NOW-timedelta(minutes=2))]},NOW)
        self.assertEqual(a["excluded_by_reason"]["event_already_started"],1)
    def test_stale_excluded(self):
        a=audit({"odds":[row(NOW+timedelta(hours=2),NOW-timedelta(minutes=20))]},NOW)
        self.assertEqual(a["excluded_by_reason"]["stale_price_over_15m"],1)
    def test_future_quote_excluded(self):
        a=audit({"odds":[row(NOW+timedelta(hours=2),NOW+timedelta(minutes=1))]},NOW)
        self.assertEqual(a["excluded_by_reason"]["future_dated_price"],1)
if __name__=="__main__":unittest.main()
