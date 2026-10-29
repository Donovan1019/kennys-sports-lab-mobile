import unittest
from scripts.ufc_elo_baseline import build
def bout(fid,winner,loser,date):
    return {"event_id":"e"+fid,"fight_id":fid,"winner":winner,"loser":loser,
            "event_date":date,"winner_verified":True}
class UFCEloTests(unittest.TestCase):
    def test_predict_before_update(self):
        rows=[bout("1","A","B","2026-01-01T12:00:00Z"),bout("2","A","B","2026-01-02T12:00:00Z")]
        report=build(rows,minimum_history=1)
        self.assertEqual(report["pre_update_evaluated_fights"],1)
        self.assertGreater(report["forecasts"][0]["winner_probability"],.5)
        self.assertFalse(report["bet_eligible"])
    def test_order_invariant_and_deduped(self):
        rows=[bout("1","A","B","2026-01-01T12:00:00Z"),bout("2","B","A","2026-01-02T12:00:00Z")]
        self.assertEqual(build(rows),build(list(reversed(rows))+rows))
    def test_future_result_not_in_past_forecast(self):
        first=bout("1","A","B","2026-01-01T12:00:00Z")
        second=bout("2","A","B","2026-01-02T12:00:00Z")
        third=bout("3","B","A","2026-01-03T12:00:00Z")
        base=build([first,second],minimum_history=1)
        more=build([first,second,third],minimum_history=1)
        self.assertEqual(base["forecasts"][0],more["forecasts"][0])
    def test_same_timestamp_does_not_leak_outcomes(self):
        past=bout("0","A","B","2026-01-01T12:00:00Z")
        same1=bout("1","A","B","2026-01-02T12:00:00Z")
        same2=bout("2","A","B","2026-01-02T12:00:00Z")
        report=build([past,same1,same2],minimum_history=1)
        self.assertEqual(report["pre_update_evaluated_fights"],2)
        self.assertEqual(report["forecasts"][0]["winner_probability"],report["forecasts"][1]["winner_probability"])
        self.assertEqual(report["historical_bouts_used"],3)
    def test_unverified_outcome_excluded(self):
        bad=bout("1","A","B","2026-01-01T12:00:00Z")
        bad["winner_verified"]=False
        self.assertEqual(build([bad])["historical_bouts_used"],0)
if __name__=="__main__":unittest.main()
