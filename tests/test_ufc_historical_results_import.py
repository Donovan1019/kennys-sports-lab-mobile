import unittest
from scripts.ufc_historical_results_import import transform
class HistoricalImportTests(unittest.TestCase):
 def row(self):
  return {"date":"2025-01-11","r_fighter":"Red A","b_fighter":"Blue B",
          "winner":"Red","no_of_rounds":"3","r_wins":"5","b_wins":"3",
          "r_avg_sig_str_landed":"4.2","b_avg_sig_str_landed":"3.9"}
 def test_settled_result_and_feature_whitelist(self):
  out=transform([self.row()],"a"*64)
  self.assertEqual(out["count"],1)
  self.assertEqual(out["fights"][0]["red_won"],1)
  self.assertEqual(out["fights"][0]["prebout_features_claimed"]["r"]["wins"],5)
  self.assertFalse(out["training_pit_certified"])
  self.assertFalse(out["bet_eligible"])
  self.assertNotIn("winner",out["fights"][0]["prebout_features_claimed"]["r"])
 def test_duplicate_fight_fails(self):
  with self.assertRaises(ValueError):transform([self.row(),self.row()],"a"*64)
 def test_unsettled_skipped(self):
  row=self.row()
  row["winner"]="Draw"
  with self.assertRaises(ValueError):transform([row],"a"*64)
 def test_invalid_rounds_not_invented(self):
  row=self.row()
  row["no_of_rounds"]=""
  self.assertIsNone(transform([row],"a"*64)["fights"][0]["scheduled_rounds"])
if __name__=="__main__":unittest.main()
