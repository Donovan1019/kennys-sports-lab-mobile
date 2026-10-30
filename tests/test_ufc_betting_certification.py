import unittest
from scripts.ufc_betting_certification import certify

class CertificationTests(unittest.TestCase):
    def setUp(self):
        self.report={"holdout_evaluated_fights":501,"holdout_brier":0.23,"holdout_log_loss":0.65,
                     "holdout_status":"CHRONOLOGICAL_EVALUATION_ONLY"}
        self.market={"independently_verified":True,"holdout_matched_fights":400,
                     "market_brier":0.24,"market_log_loss":0.67,
                     "model_brier_on_matched":0.23,"model_log_loss_on_matched":0.65}
    def test_missing_odds_fail_closed(self):
        self.assertFalse(certify(self.report)["certified"])
    def test_weak_model_rejected(self):
        self.market["model_brier_on_matched"]=0.25
        self.assertFalse(certify(self.report,self.market)["certified"])
    def test_insufficient_holdout_rejected(self):
        self.report["holdout_evaluated_fights"]=10
        self.assertFalse(certify(self.report,self.market)["certified"])
    def test_passing_fixture(self):
        self.assertTrue(certify(self.report,self.market)["certified"])
if __name__=="__main__":
    unittest.main()
