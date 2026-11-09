#!/usr/bin/env python3
import sys,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from crosscheck_nfl_injury_usage import join
def ts(d):return d.isoformat()
class CrosscheckTests(unittest.TestCase):
 def setUp(self):
  now=datetime.now(timezone.utc)
  self.usage={"profiles":[{"name":"Test Player","team":"KC","position":"QB"}]}
  self.injury={"checked_at":ts(now),"injuries":[{"team":"Kansas City Chiefs","player":"Test Player","status":"Questionable","reported_at":ts(now)}]}
 def test_candidate_not_verified(self):
  x=join(self.usage,self.injury)
  self.assertEqual(x["name_team_candidates"],1)
  self.assertFalse(x["candidates"][0]["projection_adjustment_eligible"])
  self.assertFalse(x["identity_verified"])
 def test_team_mismatch(self):
  self.injury["injuries"][0]["team"]="Buffalo Bills"
  self.assertEqual(join(self.usage,self.injury)["no_match"],1)
 def test_conflicting_statuses(self):
  self.injury["injuries"].append(dict(self.injury["injuries"][0],status="Out"))
  self.assertEqual(join(self.usage,self.injury)["ambiguous"],1)
 def test_stale_observation(self):
  self.injury["injuries"][0]["reported_at"]=ts(datetime.now(timezone.utc)-timedelta(days=1))
  self.assertEqual(join(self.usage,self.injury)["stale_or_missing"],1)
if __name__=="__main__":unittest.main()
