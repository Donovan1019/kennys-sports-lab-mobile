import unittest
from scripts.ufc_market_blend import blend_score,collect
class BlendTests(unittest.TestCase):
 def test_prior_only_weight_selection(self):
  rows=[]
  for i in range(120):
   day=f"{2020+i//12}-{i%12+1:02d}-01"
   rows.append({"date":day,"model":.9 if i%2 else .1,
      "market":.6 if i%2 else .4,"y":i%2})
  out=blend_score(rows)
  self.assertEqual(out["weight_selected_from_prior_dates"],1)
  self.assertTrue(out["beats_market_held_out"])
  self.assertFalse(out["bet_eligible"])
 def test_market_only_when_model_is_bad(self):
  rows=[]
  for i in range(120):
   rows.append({"date":f"{2020+i//12}-{i%12+1:02d}-01",
     "model":.1 if i%2 else .9,"market":.9 if i%2 else .1,"y":i%2})
  out=blend_score(rows)
  self.assertEqual(out["weight_selected_from_prior_dates"],0)
 def test_reject_insufficient_days(self):
  with self.assertRaises(ValueError):blend_score([{"date":"2025-01-01","model":.5,"market":.5,"y":1}])
if __name__=="__main__":unittest.main()
