import unittest
from scripts.ufc_round_duration_consistency import audit
class RoundDurationConsistencyTests(unittest.TestCase):
 def row(self,rounds,duration,id):
  return {"ufcstats_fight_id":id,"wide_record":{"scheduled_rounds":rounds,"fight_duration_sec":duration}}
 def test_impossible_duration_flagged(self):
  r=audit([self.row("3","901","a"),self.row("5","1500","b")])
  self.assertEqual(r["counts"]["duration_exceeds_scheduled_max"],1)
  self.assertEqual(r["counts"]["5_round_full_duration"],1)
  self.assertFalse(r["source_semantics_verified"])
 def test_missing_and_invalid(self):
  r=audit([self.row("","500","a"),self.row("7","300","b"),self.row("3","oops","c")])
  self.assertEqual(r["missing"],1)
  self.assertEqual(r["invalid"],2)
 def test_no_auto_approval(self):
  r=audit([self.row("3","900","a")])
  self.assertFalse(r["bet_eligible"])
if __name__=="__main__":unittest.main()
