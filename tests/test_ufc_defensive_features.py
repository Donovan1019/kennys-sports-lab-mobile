import unittest
from scripts.ufc_defensive_features import prior_defense
class DefenseTests(unittest.TestCase):
 def fight(self,fid,day):
  return {"ufcstats_fight_id":fid,"fighter_1_ufcstats_id":"a"*16,
  "fighter_2_ufcstats_id":"b"*16,"wide_record":{"event_date":day,
  "fight_duration_sec":"600","f1_tot_sig_str_landed":"40",
  "f2_tot_sig_str_landed":"20","f1_tot_td_landed":"2","f2_tot_td_landed":"1"}}
 def test_only_prior_fights(self):
  one=self.fight("c"*16,"2025-01-01")
  two=self.fight("d"*16,"2025-02-01")
  result=prior_defense([one,two])
  self.assertEqual(result[("c"*16,"a"*16)]["prior_defense_fights"],0)
  self.assertEqual(result[("d"*16,"a"*16)]["prior_defense_fights"],1)
  self.assertAlmostEqual(result[("d"*16,"a"*16)]["sig_absorbed_per_min"],2)
 def test_same_day_not_leaked(self):
  a=self.fight("c"*16,"2025-01-01")
  b=self.fight("d"*16,"2025-01-01")
  result=prior_defense([a,b])
  self.assertEqual(result[("d"*16,"a"*16)]["prior_defense_fights"],0)
if __name__=="__main__":unittest.main()
