import unittest
from scripts.ufc_native_fight_join import join
class NativeJoinTests(unittest.TestCase):
 def setUp(self):
  self.c=[{"fight_id":"a"*16,"ufc_event_id":"b"*16,"f1_id":"c"*16,"f2_id":"d"*16}]
 def test_exact_native_id(self):
  r=join(self.c,[{"fight_id":"a"*16,"sig_strikes":"27"}])
  self.assertEqual(r["status"],"JOINED")
  self.assertEqual(r["matched"],1)
  self.assertEqual(r["records"][0]["wide_record"]["sig_strikes"],"27")
 def test_no_name_based_fallback(self):
  r=join(self.c,[{"fighter":"A","date":"2025-01-01"}])
  self.assertEqual(r["status"],"SCHEMA_BLOCKED")
  self.assertEqual(r["matched"],0)
 def test_unmatched_does_not_fabricate(self):
  r=join(self.c,[{"fight_id":"e"*16}])
  self.assertEqual(r["status"],"NO_MATCHES")
  self.assertEqual(r["unmatched"],1)
 def test_duplicate_id_rejected(self):
  with self.assertRaises(ValueError):join(self.c,[{"fight_id":"a"*16},{"fight_id":"a"*16}])
 def test_crosswalk_duplicate_rejected(self):
  with self.assertRaises(ValueError):join(self.c+self.c,[{"fight_id":"a"*16}])
if __name__=="__main__":unittest.main()
