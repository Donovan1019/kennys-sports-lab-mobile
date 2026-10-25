import unittest
from scripts.ufc_pinned_cohort_gate import validate,FIELDS
class CohortGateTests(unittest.TestCase):
 def setUp(self):
  self.expected={"joined_eligible_fights":6743,"holdout_date_scoped_fights":1353,
   "holdout_fight_ids_sha256":"a"*64,"evaluated_fights":768,"holdout_start_date":"2024-03-30"}
  self.actual=dict(self.expected,source_snapshot_locked=True,source_drift_gate="PASS")
 def test_accept_exact_match(self):
  self.assertEqual(validate(self.expected,self.actual)["cohort_gate"],"PASS")
 def test_reject_each_mismatch(self):
  for field in FIELDS:
   with self.subTest(field=field):
    modified=dict(self.actual)
    modified[field]=0 if isinstance(modified[field],str) else modified[field]+1
    with self.assertRaisesRegex(ValueError,"COHORT_DRIFT_BLOCKED"):validate(self.expected,modified)
 def test_reject_unpinned(self):
  modified=dict(self.actual,source_snapshot_locked=False)
  with self.assertRaisesRegex(ValueError,"SOURCE_NOT_PINN"):validate(self.expected,modified)
if __name__=="__main__":unittest.main()
