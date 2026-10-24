import unittest
from scripts.ufc_calibration_diagnostics import calibration,temporal_robustness
class CalibrationTests(unittest.TestCase):
 def test_perfect_calibration(self):
  out=calibration([(.2,0),(.8,1)])
  self.assertEqual(sum(b["count"] for b in out["bins"]),2)
  self.assertGreaterEqual(out["expected_calibration_error"],0)
 def test_wilson_bounds(self):
  out=calibration([(.7,1)]*10+[(.7,0)]*10)
  row=out["bins"][0]
  self.assertLess(row["wilson_95_low"],.5)
  self.assertGreater(row["wilson_95_high"],.5)
 def test_rejects_bad_probability(self):
  with self.assertRaises(ValueError):calibration([(1.2,1)])
 def test_rejects_empty(self):
  with self.assertRaises(ValueError):calibration([])
 def test_temporal_folds(self):
  rows=[{"fight_id":str(i),"date":f"{2020+i//12}-{i%12+1:02d}-01",
         "x":[1 if i%2 else -1,.2,0],"y":i%2} for i in range(120)]
  out=temporal_robustness(rows)
  self.assertEqual(len(out["folds"]),3)
  self.assertTrue(out["research_only"])
if __name__=="__main__":unittest.main()
