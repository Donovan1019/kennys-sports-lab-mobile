import unittest
from scripts.ufc_mirror_fight_schema_audit import inspect

class Tests(unittest.TestCase):
 def test_reports_missing_join_fields(self):
  result=inspect([{"FIGHTER":"A","SIG.STR.":"5 of 10","TD":"0 of 1","CTRL":"0:10"}])
  self.assertFalse(result["can_generate_point_in_time_training_rows"])
  self.assertIn("fight_id",result["missing_historical_fields"])
  self.assertIn("fight_time",result["missing_historical_fields"])
 def test_detects_schema_candidates(self):
  result=inspect([{"FIGHTER":"A","SIG.STR.":"5 of 10","TD":"0 of 1","CTRL":"0:10",
                   "FIGHT_ID":"f1","DATE":"2025-01-01","ROUND":"1",
                   "ROUND_DURATION":"5:00","RESULT":"W"}])
  self.assertTrue(result["can_generate_point_in_time_training_rows"])
 def test_rejects_missing_stats(self):
  with self.assertRaises(ValueError):inspect([{"FIGHTER":"A"}])
if __name__=="__main__":unittest.main()
