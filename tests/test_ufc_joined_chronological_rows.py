import unittest
from scripts.ufc_joined_chronological_rows import convert
from scripts.ufc_historical_prefix_features import build
class ChronologicalRowsTests(unittest.TestCase):
 def record(self,fid,when,sig="20",winner="f1"):
  return {"ufcstats_fight_id":fid,"fighter_1_ufcstats_id":"a"*16,
   "fighter_2_ufcstats_id":"b"*16,
   "wide_record":{"event_date":when,"fight_duration_sec":"600","f1_id":"a"*16,
   "f2_id":"b"*16,"winner":winner,"f1_tot_sig_str_landed":sig,
   "f1_tot_sig_str_att":"100","f1_tot_td_landed":"1","f1_tot_td_att":"3",
   "f2_tot_sig_str_landed":"30","f2_tot_sig_str_att":"80",
   "f2_tot_td_landed":"0","f2_tot_td_att":"1"}}
 def test_exact_fighter_rows_and_prior_fights(self):
  data=convert([self.record("c"*16,"2025-01-01"),self.record("d"*16,"2025-02-01")])
  self.assertEqual(data["fighter_rows"],4)
  features=build(data["rows"])
  a=[x for x in features if x["fighter_id"]=="a"*16]
  self.assertEqual([x["prior_fights"] for x in a],[0,1])
  self.assertEqual(a[1]["sig_landed_per_min"],2)
 def test_no_contest_not_training_exposure(self):
  data=convert([self.record("c"*16,"2025-01-01",winner="NC")])
  self.assertEqual(data["fighter_rows"],0)
 def test_rejects_fighter_identity_mismatch(self):
  record=self.record("c"*16,"2025-01-01")
  record["wide_record"]["f1_id"]="e"*16
  self.assertEqual(convert([record])["fighter_rows"],0)
if __name__=="__main__":unittest.main()
