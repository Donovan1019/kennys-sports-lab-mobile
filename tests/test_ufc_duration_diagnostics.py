import unittest
from scripts.ufc_duration_diagnostics import evaluate
class DurationDiagnosticsTests(unittest.TestCase):
    def rows(self):
        out=[]
        for i in range(20):
            for fighter in ("A","B"):
                out.append({"fight_id":str(i),"fighter_id":fighter,
                  "fight_time":"2025-%02d-01T00:00:00Z"%(i%12+1) if i<12 else "2026-%02d-01T00:00:00Z"%(i-11),
                  "active_seconds":str(300+i*15)})
        return out
    def test_split_and_dedup(self):
        r=evaluate(self.rows())
        self.assertEqual(r["train"]["n"]+r["test"]["n"],20)
        self.assertFalse(r["finish_hazard_estimated"])
        self.assertFalse(r["bet_eligible"])
        self.assertGreater(r["test_mean_absolute_error_seconds"],0)
    def test_conflicting_same_fight(self):
        rows=self.rows();rows[1]["active_seconds"]="900"
        with self.assertRaises(ValueError):evaluate(rows)
    def test_same_date_never_leaks(self):
        rows=self.rows()
        for row in rows:row["fight_time"]="2025-01-01T00:00:00Z"
        with self.assertRaises(ValueError):evaluate(rows)
if __name__=="__main__":unittest.main()
