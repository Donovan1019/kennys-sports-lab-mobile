import unittest
from scripts.ufc_historical_prefix_features import build

class Tests(unittest.TestCase):
 def row(self,fight,when,landed,attempted,seconds=300,settled="true"):
  return {"fight_id":fight,"fighter_id":"A","fight_time":when,"settled":settled,
          "sig_landed":str(landed),"sig_attempted":str(attempted),
          "takedowns_landed":"1","takedowns_attempted":"2","active_seconds":str(seconds)}
 def test_no_current_fight_leakage(self):
  a=self.row("f1","2025-01-01T00:00:00Z",10,20)
  b=self.row("f2","2025-02-01T00:00:00Z",100,120)
  x=build([b,a])
  self.assertEqual(x[0]["prior_fights"],0)
  self.assertIsNone(x[0]["sig_landed_per_min"])
  self.assertEqual(x[1]["prior_fights"],1)
  self.assertEqual(x[1]["sig_landed_per_min"],2)
 def test_same_timestamp_not_in_history(self):
  a=self.row("f1","2025-01-01T00:00:00Z",10,20)
  b=self.row("f2","2025-01-01T00:00:00Z",100,120)
  self.assertEqual([x["prior_fights"] for x in build([a,b])],[0,0])
 def test_unsettled_not_in_history(self):
  a=self.row("f1","2025-01-01T00:00:00Z",10,20,settled="false")
  b=self.row("f2","2025-02-01T00:00:00Z",100,120)
  self.assertEqual(build([a,b])[1]["prior_fights"],0)
 def test_reject_invalid_counts(self):
  a=self.row("f1","2025-01-01T00:00:00Z",30,20)
  with self.assertRaises(ValueError):build([a])
 def test_reject_duplicates(self):
  a=self.row("f1","2025-01-01T00:00:00Z",10,20)
  with self.assertRaises(ValueError):build([a,a])
if __name__=="__main__":unittest.main()
