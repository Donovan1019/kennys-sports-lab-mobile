import unittest
from scripts.ufc_defensive_market_blend import score
class DefensiveMarketBlendTests(unittest.TestCase):
 def rows(self,model_good):
  rows=[]
  for i in range(120):
   y=i%2
   rows.append({"date":f"{2020+i//12}-{i%12+1:02d}-01",
     "p":(.9 if y else .1) if model_good else (.1 if y else .9),
     "market":.7 if y else .3,"y":y})
  return rows
 def test_good_model_gets_weight(self):
  result=score(self.rows(True))
  self.assertEqual(result["selected_defensive_model_weight"],1)
  self.assertTrue(result["beats_market_held_out"])
 def test_bad_model_reverts_to_market(self):
  result=score(self.rows(False))
  self.assertEqual(result["selected_defensive_model_weight"],0)
  self.assertFalse(result["beats_market_held_out"])
 def test_short_history_rejected(self):
  with self.assertRaises(ValueError):score([{"date":"2025-01-01","p":.5,"market":.5,"y":1}])
if __name__=="__main__":unittest.main()
