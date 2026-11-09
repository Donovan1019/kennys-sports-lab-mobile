#!/usr/bin/env python3
import sys,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_nfl_injury_observation_quality import audit
class QualityTests(unittest.TestCase):
 def setUp(self):
  self.now=datetime(2026,11,9,18,tzinfo=timezone.utc)
  self.payload={"checked_at":self.now.isoformat(),"injuries":[{"team_id":"1","player":"A","status":"Out","reported_at":(self.now-timedelta(days=2)).isoformat()}]}
 def test_old_out_not_confirmed(self):
  r=audit(self.payload,self.now)
  self.assertEqual(r["report_age_buckets"]["LAST_7_DAYS"],1)
  self.assertFalse(r["game_day_availability_verified"])
  self.assertFalse(r["betting_eligible"])
 def test_conflicting_statuses(self):
  self.payload["injuries"].append(dict(self.payload["injuries"][0],status="Questionable"))
  self.assertEqual(audit(self.payload,self.now)["conflicting_name_team_statuses"],1)
 def test_future_report_invalid(self):
  self.payload["injuries"][0]["reported_at"]=(self.now+timedelta(hours=1)).isoformat()
  self.assertEqual(audit(self.payload,self.now)["report_age_buckets"]["INVALID_TIMESTAMP"],1)
 def test_stale_snapshot(self):
  self.payload["checked_at"]=(self.now-timedelta(days=1)).isoformat()
  self.assertFalse(audit(self.payload,self.now)["feed_fresh"])
if __name__=="__main__":unittest.main()
