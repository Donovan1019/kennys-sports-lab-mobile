import unittest
from scripts.ufc_scheduled_rounds_audit import audit
class AuditTests(unittest.TestCase):
 def test_missing_rounds_never_assumed(self):
  r=audit([{"wide_record":{"fight_duration_sec":"900"}}])
  self.assertFalse(r["complete_and_valid"])
  self.assertFalse(r["ready_for_duration_model"])
  self.assertEqual(r["scheduled_rounds_counts"]["missing"],1)
 def test_candidate_not_automatically_verified(self):
  r=audit([{"wide_record":{"scheduled_rounds":"5"}}])
  self.assertTrue(r["complete_and_valid"])
  self.assertFalse(r["verified_source_semantics"])
  self.assertFalse(r["ready_for_duration_model"])
 def test_conflicting_fields_rejected(self):
  r=audit([{"wide_record":{"scheduled_rounds":"3","num_rounds":"5"}}])
  self.assertEqual(r["invalid_or_conflicting"],1)
  self.assertFalse(r["complete_and_valid"])
if __name__=="__main__":unittest.main()
