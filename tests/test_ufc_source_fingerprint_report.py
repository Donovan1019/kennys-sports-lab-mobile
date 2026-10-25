"""Tests for the fail-closed UFC source fingerprint contract."""
import unittest
from scripts.ufc_early_duration_probability import evaluate
class SourceFingerprintTests(unittest.TestCase):
 def test_source_hashes_preserved_in_report(self):
  rows=[]
  for i in range(30):
   day="2024-01-%02d"%(i+1) if i<28 else "2024-02-%02d"%(i-27)
   rows.append({"ufcstats_fight_id":str(i),"wide_record":{"event_date":day,"f1_id":"a","f2_id":"b","fight_duration_sec":"600"}})
  hashes={"crosswalk":"a"*64,"wide":"b"*64}
  report=evaluate(rows,source_hashes=hashes)
  self.assertEqual(report["source_sha256"],hashes)
  self.assertFalse(report["production_promotion_allowed"])
if __name__=="__main__":unittest.main()
