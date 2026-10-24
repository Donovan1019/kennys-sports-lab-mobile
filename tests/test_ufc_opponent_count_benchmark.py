import unittest
from scripts.ufc_opponent_count_benchmark import evaluate
class OpponentBenchmarkTests(unittest.TestCase):
    def rows(self):
        out=[]
        for i in range(20):
            date="2025-%02d-01T00:00:00Z"%(i+1) if i<12 else "2026-%02d-01T00:00:00Z"%(i-11)
            for fighter in ("A","B"):
                out.append({"fight_id":str(i),"fighter_id":fighter,"fight_time":date,
                  "active_seconds":"300","settled":"true","sig_landed":str(10+i),
                  "sig_attempted":str(20+i),"takedowns_landed":"1","takedowns_attempted":"2"})
        return out
    def test_paired_benchmark(self):
        result=evaluate(self.rows())
        self.assertEqual(result["markets"]["sig_landed"]["n"],8)
        self.assertFalse(result["weight_tuned_on_holdout"])
        self.assertTrue(result["oracle_duration"])
        self.assertFalse(result["bet_eligible"])
    def test_zero_weight_same_baseline(self):
        result=evaluate(self.rows(),opponent_weight=0)
        for market in result["markets"].values():
            self.assertAlmostEqual(market["mae_improvement"],0)
    def test_invalid_pair(self):
        with self.assertRaises(ValueError):evaluate(self.rows()[:-1])
    def test_no_earlier_training_date(self):
        rows=self.rows()
        for row in rows:row["fight_time"]="2025-01-01T00:00:00Z"
        with self.assertRaises(ValueError):evaluate(rows)
if __name__=="__main__":unittest.main()
