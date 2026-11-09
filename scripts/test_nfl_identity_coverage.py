#!/usr/bin/env python3
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_nfl_identity_coverage import audit
class CoverageTests(unittest.TestCase):
 def setUp(self):
  self.stats={"players":[{"id":"n1"}]}
  self.usage={"profiles":[{"nflverse_player_id":"n1"}]}
  self.inj={"injuries":[{"espn_athlete_id":"e1"}]}
  self.cross={"name_team_candidates":1,"historical_name_team_candidates":0,"no_match":0,"ambiguous":0,"injury_feed_fresh":True}
 def test_fail_closed(self):
  r=audit(self.stats,self.usage,self.inj,self.cross)
  self.assertFalse(r["betting_eligible"])
  self.assertFalse(r["identity_crosswalk_verified"])
  self.assertEqual(r["unique_espn_ids_observed"],1)
 def test_duplicate_profile_ids_rejected(self):
  self.usage["profiles"].append({"nflverse_player_id":"n1"})
  with self.assertRaises(ValueError):audit(self.stats,self.usage,self.inj,self.cross)
 def test_mismatched_counts_rejected(self):
  self.cross["no_match"]=1
  with self.assertRaises(ValueError):audit(self.stats,self.usage,self.inj,self.cross)
if __name__=="__main__":unittest.main()
