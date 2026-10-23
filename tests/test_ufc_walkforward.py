import unittest
from scripts.ufc_walkforward import audit
def prediction(fid="1",p=.7,generated="2026-10-01T10:00:00Z",start="2026-10-01T12:00:00Z"):
    return {"fight_id":fid,"generated_at":generated,"start_time":start,
            "red_win_probability":p,"research_only":True,"model_version":"test-1"}
def result(fid="1",winner="red",completed="2026-10-01T13:00:00Z"):
    return {"fight_id":fid,"winner":winner,"completed_at":completed}
class UFCWalkForwardTests(unittest.TestCase):
    def test_valid_pregame_score(self):
        a=audit([prediction()],[result()])
        self.assertEqual(a["graded"],1)
        self.assertAlmostEqual(a["brier_score"],.09)
        self.assertEqual(a["calibration_status"],"INSUFFICIENT_SAMPLE")
        self.assertFalse(a["bet_eligible"])
        self.assertIsNone(a["roi"])
    def test_rejects_post_start_forecast(self):
        a=audit([prediction(generated="2026-10-01T12:01:00Z")],[result()])
        self.assertEqual(a["graded"],0)
    def test_duplicate_forecast_does_not_double_count(self):
        a=audit([prediction(),prediction()],[result()])
        self.assertEqual(a["graded"],1)
        self.assertEqual(len(a["blocked"]),1)
    def test_missing_outcome_and_naive_timestamp(self):
        self.assertEqual(audit([prediction()],[])["graded"],0)
        self.assertEqual(audit([prediction(generated="2026-10-01T10:00:00")],[result()])["graded"],0)
    def test_rejects_impossible_probabilities(self):
        self.assertEqual(audit([prediction(p=1.2)],[result()])["graded"],0)
if __name__=="__main__":unittest.main()
