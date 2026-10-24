import unittest
from scripts.ufc_bout_monte_carlo import simulate,poisson
import random
RATES={"sig_landed":20.0,"sig_attempted":40.0,"takedowns_landed":1.0,"takedowns_attempted":2.0}
class UFCMonteCarloTests(unittest.TestCase):
    def test_reproducibility_and_bounds(self):
        a=simulate(RATES,3,draws=1000,seed=7,thresholds={"sig_landed":49.5})
        self.assertEqual(a,simulate(RATES,3,draws=1000,seed=7,thresholds={"sig_landed":49.5}))
        self.assertGreaterEqual(a["mean_active_rounds"],1)
        self.assertLessEqual(a["mean_active_rounds"],3)
        self.assertTrue(0<=a["markets"]["sig_landed"]["over_threshold_probability"]<=1)
        self.assertFalse(a["bet_eligible"])
    def test_zero_and_no_finish(self):
        rates={key:0 for key in RATES}
        result=simulate(rates,5,draws=100,finish_hazard=0)
        self.assertEqual(result["mean_active_rounds"],5)
        self.assertEqual(result["markets"]["sig_landed"]["mean"],0)
        self.assertEqual(poisson(random.Random(1),0),0)
    def test_invalid_inputs(self):
        for rounds in (0,4,None):
            with self.assertRaises(ValueError):simulate(RATES,rounds)
        with self.assertRaises(ValueError):simulate({**RATES,"sig_landed":float("nan")},3)
        with self.assertRaises(ValueError):simulate(RATES,3,draws=10)
if __name__=="__main__":unittest.main()
