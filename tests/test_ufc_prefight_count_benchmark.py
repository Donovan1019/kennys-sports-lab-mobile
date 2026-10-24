import unittest
from scripts.ufc_prefight_count_benchmark import evaluate
class PrefightBenchmarkTests(unittest.TestCase):
    def rows(self):
        out=[]
        for i in range(20):
            date="2025-%02d-01T00:00:00Z"%(i+1) if i<12 else "2026-%02d-01T00:00:00Z"%(i-11)
            for fighter in ("A","B"):
                out.append({"fight_id":str(i),"fighter_id":fighter,"fight_time":date,
                  "active_seconds":str(240+5*i),"settled":"true","sig_landed":str(10+i),
                  "sig_attempted":str(20+i),"takedowns_landed":"1","takedowns_attempted":"2"})
        return out
    def test_no_oracle(self):
        r=evaluate(self.rows())
        self.assertFalse(r["oracle_duration"])
        self.assertIsNotNone(r["duration_mae_seconds"])
        self.assertEqual(r["markets"]["sig_landed"]["n"],8)
        self.assertEqual(r["duration_evaluated_fights"],4)
        self.assertGreaterEqual(r["duration_rmse_seconds"],r["duration_mae_seconds"])
        self.assertIn("shrunk_mae_seconds",r["duration_shrinkage_candidate"])
        self.assertFalse(r["duration_shrinkage_candidate"]["weight_tuned_on_holdout"])
        self.assertFalse(r["bet_eligible"])
    def test_zero_weight_matches_baseline(self):
        r=evaluate(self.rows(),opponent_weight=0)
        for market in r["markets"].values():self.assertAlmostEqual(market["mae_improvement"],0)
    def test_same_day_blocked(self):
        rows=self.rows()
        for row in rows:row["fight_time"]="2025-01-01T00:00:00Z"
        with self.assertRaises(ValueError):evaluate(rows)
    def test_current_fight_duration_not_used_for_prediction(self):
        rows=self.rows();a=evaluate(rows)
        for row in rows:
            if row["fight_id"]=="19":row["active_seconds"]="1200"
        b=evaluate(rows)
        self.assertNotEqual(a["duration_mae_seconds"],b["duration_mae_seconds"])
        # Changing the held-out outcome cannot change earlier predictions.
        self.assertEqual(a["markets"]["sig_landed"]["n"],b["markets"]["sig_landed"]["n"])
if __name__=="__main__":unittest.main()
