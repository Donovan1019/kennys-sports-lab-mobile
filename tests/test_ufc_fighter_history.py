import datetime as dt
import unittest
from scripts.ufc_fighter_history import summarize
NOW=dt.datetime(2026,10,23,tzinfo=dt.timezone.utc)
def row(fid="1",method="KO/TKO",date="2026-10-01T20:00:00Z"):
    return {"event_id":"ev1","fight_id":fid,"event_date":date,"winner":"A","loser":"B","method":method,"source_url":"https://example.org/source"}
class UFCHistoryTests(unittest.TestCase):
    def test_deduplication_and_no_future_leakage(self):
        result=summarize([row(),row(),row("2","Decision"),row("3",date="2026-12-01T20:00:00Z")],NOW)
        self.assertEqual(result["verified_result_count"],2)
        a=next(f for f in result["fighters"] if f["name"]=="A")
        self.assertEqual(a["wins"],2)
        self.assertEqual(a["historical_win_method_rates"]["KO/TKO"],0.5)
        self.assertFalse(result["bet_eligible"])
    def test_invalid_results_are_rejected(self):
        self.assertEqual(summarize([row(method="Unknown"),row(date="bad")],NOW)["verified_result_count"],0)
    def test_losers_not_given_win_method_rates(self):
        b=next(f for f in summarize([row()],NOW)["fighters"] if f["name"]=="B")
        self.assertIsNone(b["historical_win_method_rates"]["KO/TKO"])
if __name__=="__main__":unittest.main()
