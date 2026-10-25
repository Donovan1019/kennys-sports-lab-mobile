import unittest
from scripts.ufc_duration_uncertainty import evaluate,quantile
class DurationUncertaintyTests(unittest.TestCase):
 def records(self):
  out=[]
  for i in range(50):
   day="2024-01-%02d"%(i+1) if i<28 else "2024-02-%02d"%(i-27)
   out.append({"ufcstats_fight_id":str(i),"wide_record":{"event_date":day,"f1_id":"a","f2_id":"b","fight_duration_sec":str(300+(i%5)*100)}})
  return out
 def test_quantile(self):
  self.assertEqual(quantile([1,2,3,4,5],.8),5)
 def test_holdout_coverage_research_only(self):
  r=evaluate(self.records(),min_residuals=3)
  self.assertGreater(r["evaluated_fights"],0)
  self.assertGreaterEqual(r["empirical_coverage"],0)
  self.assertLessEqual(r["empirical_coverage"],1)
  self.assertFalse(r["production_promotion_allowed"])
 def test_reject_bad_parameters(self):
  with self.assertRaises(ValueError):evaluate(self.records(),min_residuals=0)
if __name__=="__main__":unittest.main()
