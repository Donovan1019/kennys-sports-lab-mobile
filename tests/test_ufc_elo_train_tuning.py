import unittest
from scripts.ufc_elo_train_tuning import run_elo, metrics

class EloTuneTests(unittest.TestCase):
    def test_same_day_prediction_uses_prior_day_only(self):
        import datetime as dt
        d1=dt.date(2020,1,1)
        d2=dt.date(2020,1,2)
        x=run_elo({d1:[("A","B"),("A","B")],d2:[("B","A")]},24,1)
        self.assertEqual(len(x),1)
        self.assertEqual(x[0][0],d2)
    def test_metric(self):
        self.assertEqual(metrics([0.5])["brier"],0.25)
if __name__=="__main__":
    unittest.main()
