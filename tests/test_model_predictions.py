import unittest,tempfile
from pathlib import Path
from scripts.model_predictions import validate_prediction,publish
class PublicationTests(unittest.TestCase):
 def test_rejects_market_implied(self):
  with self.assertRaises(ValueError):validate_prediction({'model_probability':.8},[])
 def test_empty_candidates_publish_empty(self):
  with tempfile.TemporaryDirectory() as d:
   result=publish([],[],Path(d)/'predictions.json')
   self.assertEqual(result['predictions'],[])
 def test_requires_backtest(self):
  row={'sport':'americanfootball_nfl','event_id':'abc','market':'h2h','selection':'Team A','point':None}
  p={**row,'model_version':'test','input_timestamp':'2026-10-19T12:00:00+00:00','model_probability':.6,'simulations':10000,'status':'validated','is_forecast':True,'backtest':{'method':'walk_forward','passed':False,'sample_size':200,'brier':.2}}
  with self.assertRaises(ValueError):validate_prediction(p,[row])
if __name__=='__main__':unittest.main()
