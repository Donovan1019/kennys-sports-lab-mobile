import unittest
from scripts.ufc_source_id_crosswalk import build
class CrosswalkTests(unittest.TestCase):
 def row(self):
  return {"fight_id":"a"*16,"ufc_event_id":"b"*16,"f1_id":"c"*16,"f2_id":"d"*16,
          "mmad_decision_id":"123","mmad_name_sim":"0.97","mmad_day_gap":"0","mmad_total_agree":"2"}
 def test_high_confidence_link(self):
  out=build([self.row()],"f"*64)
  self.assertEqual(out["fights"][0]["mma_decisions_match_quality"],"HIGH")
  self.assertFalse(out["bet_eligible"])
 def test_weak_match_requires_review(self):
  row=self.row();row["mmad_name_sim"]="0.4"
  self.assertEqual(build([row],"f"*64)["fights"][0]["mma_decisions_match_quality"],"REVIEW")
 def test_rejects_duplicate_fights(self):
  with self.assertRaises(ValueError):build([self.row(),self.row()],"f"*64)
 def test_rejects_invalid_id(self):
  row=self.row();row["fight_id"]="not-id"
  with self.assertRaises(ValueError):build([row],"f"*64)
 def test_unlinked_not_confident(self):
  row=self.row();row["mmad_decision_id"]=""
  self.assertEqual(build([row],"f"*64)["fights"][0]["mma_decisions_match_quality"],"UNLINKED")
if __name__=="__main__":unittest.main()
