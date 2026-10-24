import unittest
from scripts.ufc_market_benchmark import market_probability,benchmark
class MarketTests(unittest.TestCase):
 def test_valid_no_vig_market(self):
  p=market_probability({"wide_record":{"f1_close_prob_novig":"0.65","f2_close_prob_novig":"0.35"}})
  self.assertAlmostEqual(p,.65)
 def test_reject_missing(self):
  self.assertIsNone(market_probability({"wide_record":{}}))
 def test_reject_unbalanced_market(self):
  self.assertIsNone(market_probability({"wide_record":{"f1_close_prob_novig":".9","f2_close_prob_novig":".9"}}))
 def test_paired_market_comparison(self):
  import hashlib
  rows=[]
  records=[]
  for i in range(120):
   fid=f"{i:016x}"
   rows.append({"fight_id":fid,"date":f"{2020+i//12}-{i%12+1:02d}-01","x":[.2,0,0],"y":i%2})
   records.append({"ufcstats_fight_id":fid,"wide_record":{"f1_close_prob_novig":".55","f2_close_prob_novig":".45"}})
  result=benchmark(rows,records)
  self.assertGreater(result["paired_test_fights"],0)
  self.assertFalse(result["profitability_tested"])
if __name__=="__main__":unittest.main()
