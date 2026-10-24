import unittest
from scripts.ufc_count_holdout import evaluate
class HoldoutTests(unittest.TestCase):
    def rows(self):
        out=[]
        for i in range(20):
            day="2025-%02d-01T00:00:00Z"%(i+1) if i<12 else "2026-%02d-01T00:00:00Z"%(i-11)
            # First 12 must be valid months.
            for fighter in ("A","B"):
                out.append({"fight_id":str(i),"fighter_id":fighter,"fight_time":day,
                  "active_seconds":"300","settled":"true","sig_landed":str(i+10),
                  "sig_attempted":str(i+20),"takedowns_landed":"1","takedowns_attempted":"2"})
        return out
    def test_holdout_and_provenance(self):
        result=evaluate(self.rows())
        self.assertTrue(result["duration_oracle"])
        self.assertFalse(result["bet_eligible"])
        self.assertEqual(result["markets"]["sig_landed"]["n"],8)
        self.assertEqual(result["markets"]["sig_landed"]["distinct_fights"],4)
    def test_missing_pair(self):
        rows=self.rows()[:-1]
        with self.assertRaises(ValueError):evaluate(rows)
    def test_same_date_no_leakage(self):
        rows=self.rows()
        for row in rows:row["fight_time"]="2025-01-01T00:00:00Z"
        with self.assertRaises(ValueError):evaluate(rows)
if __name__=="__main__":unittest.main()
