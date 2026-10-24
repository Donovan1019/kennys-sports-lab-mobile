import unittest
from scripts.ufc_joined_feature_audit import audit
class AuditTests(unittest.TestCase):
 def test_detects_required_fields(self):
  rows=[{"wide_record":{"fight_id":"a"*16,"event_date":"2025-01-01",
     "r_sig_str_landed":"32","b_td_landed":"2","last_round_time":"5:00",
     "winner":"Red","r_fighter_id":"b"*16}}]
  result=audit(rows)
  self.assertEqual(result["joined_fights"],1)
  self.assertEqual(result["missing_required_groups"],[])
  self.assertFalse(result["can_construct_pre_fight_features"])
 def test_reports_missing(self):
  result=audit([{"wide_record":{"fight_id":"a"*16}}])
  self.assertIn("strike_counts",result["missing_required_groups"])
 def test_empty_rejected(self):
  with self.assertRaises(ValueError):audit([])
if __name__=="__main__":unittest.main()
