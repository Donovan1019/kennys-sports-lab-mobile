import unittest
from scripts.ufc_format_duration_benchmark import evaluate
class FormatDurationTests(unittest.TestCase):
 def data(self):
  rows=[]
  for i in range(30):
   day="2025-%02d-01"%(i+1) if i<12 else "2026-%02d-01"%(i-11) if i<24 else "2027-%02d-01"%(i-23)
   fmt="3" if i%4 else "5"
   rows.append({"ufcstats_fight_id":str(i),"wide_record":{"event_date":day,"f1_id":"a","f2_id":"b","scheduled_rounds":fmt,"fight_duration_sec":str(600 if fmt=="3" else 1200)}})
  return rows
 def test_prior_only_and_research_only(self):
  r=evaluate(self.data())
  self.assertGreater(r["total_eligible_fights"],0)
  self.assertFalse(r["duration_oracle"])
  self.assertFalse(r["production_promotion_allowed"]) 
  self.assertIn(r["decision"],("REJECT","RESEARCH_ONLY"))
  self.assertFalse(r["scheduled_rounds_source_semantics_verified"])
 def test_no_prior_day_rejected(self):
  rows=self.data()
  for item in rows:item["wide_record"]["event_date"]="2025-01-01"
  with self.assertRaises(ValueError):evaluate(rows)
 def test_same_format_history_required(self):
  rows=self.data()
  r=evaluate(rows,min_prior=100)
  self.assertEqual(r["total_eligible_fights"],0) 
  self.assertEqual(r["decision"],"REJECT")
if __name__=="__main__":unittest.main()
