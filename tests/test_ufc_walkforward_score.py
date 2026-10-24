import unittest
from datetime import datetime, timedelta, timezone
from scripts.ufc_walkforward_score import evaluate

class TestUfcWalkforward(unittest.TestCase):
    def row(self,fid,p,y):
        return {"fight_id":fid,"fight_time":"2026-01-02T20:00:00Z",
                "prediction_time":"2026-01-01T20:00:00Z",
                "model_version":"test-v1","predicted_red_win":str(p),"red_won":str(y)}
    def test_perfect_predictions_better_than_baseline(self):
        r=evaluate([self.row("1",.99,1),self.row("2",.01,0)])
        self.assertLess(r["brier"],r["baseline_brier_50pct"])
        self.assertLess(r["log_loss"],r["baseline_log_loss_50pct"])
        self.assertEqual(r["sample_size"],2)
    def test_rejects_leakage(self):
        row=self.row("1",.7,1)
        row["prediction_time"]=row["fight_time"]
        with self.assertRaises(ValueError):evaluate([row])
    def test_rejects_duplicates(self):
        with self.assertRaises(ValueError):evaluate([self.row("1",.7,1),self.row("1",.6,0)])
    def test_rejects_invalid_probability(self):
        with self.assertRaises(ValueError):evaluate([self.row("1",1.1,1)])
    def test_rejects_empty(self):
        with self.assertRaises(ValueError):evaluate([])

if __name__=="__main__":unittest.main()
