import unittest
from scripts.ufc_opponent_walkforward import vector,examples,evaluate
class WalkForwardTests(unittest.TestCase):
 def row(self,fid,day,x,y):
  return {"fight_id":fid,"date":day,"x":x,"y":y}
 def test_opponent_differentials(self):
  a={"prior_fights":3,"sig_landed_per_min":5,"sig_accuracy":.6,"takedowns_per_15min":2}
  b={"prior_fights":3,"sig_landed_per_min":3,"sig_accuracy":.4,"takedowns_per_15min":1}
  self.assertEqual(vector(a,b),[.5,.4,1/3])
 def test_no_history_no_projection(self):
  a={"prior_fights":1}
  self.assertIsNone(vector(a,a))
 def test_out_of_sample(self):
  rows=[self.row(str(i),f"2025-01-{i+1:02d}",[1,0,0],i%2) for i in range(12)]
  r=evaluate(rows)
  self.assertGreater(r["test_fights"],0)
  self.assertLess(r["training_fights"],len(rows))
  self.assertFalse(r["bet_eligible"])
 def test_invalid_split(self):
  with self.assertRaises(ValueError):evaluate([],train_fraction=1)
 def test_unknown_winner_excluded(self):
  a="a"*16;b="b"*16;fid="c"*16
  record={"ufcstats_fight_id":fid,"fighter_1_ufcstats_id":a,"fighter_2_ufcstats_id":b,
    "wide_record":{"winner":"Draw"}}
  feature={"prior_fights":3,"fight_time":"2025-01-01T00:00:00Z",
    "sig_landed_per_min":4,"sig_accuracy":.5,"takedowns_per_15min":1}
  rows,exc=examples([record],[{"fight_id":fid,"fighter_id":a,**feature},{"fight_id":fid,"fighter_id":b,**feature}])
  self.assertEqual(len(rows),0)
  self.assertEqual(exc["winner_not_native_fighter_id"],1)
if __name__=="__main__":unittest.main()
