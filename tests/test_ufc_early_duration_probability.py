import unittest
from scripts.ufc_early_duration_probability import evaluate
class EarlyDurationTests(unittest.TestCase):
 def records(self):
  rows=[]
  for i in range(30):
   day="2024-01-%02d"%(i+1) if i<28 else "2024-02-%02d"%(i-27)
   rows.append({"ufcstats_fight_id":str(i),"wide_record":{"event_date":day,"f1_id":"a","f2_id":"b","fight_duration_sec":str(150 if i%3==0 else 800)}})
  return rows
 def test_brier_and_research_gate(self):
  r=evaluate(self.records())
  self.assertGreater(r["evaluated_fights"],0)
  self.assertGreaterEqual(r["candidate_fighter_prior"]["brier"],0)
  self.assertFalse(r["production_promotion_allowed"])
  self.assertIn(r["decision"],("REJECT","RESEARCH_ONLY"))
 def test_same_day_no_prior(self):
  rows=self.records()
  for row in rows:row["wide_record"]["event_date"]="2024-01-01"
  with self.assertRaises(ValueError):evaluate(rows)
 def test_reject_no_sample(self):
  r=evaluate(self.records(),min_prior=100)
  self.assertEqual(r["decision"],"REJECT")
if __name__=="__main__":unittest.main()
