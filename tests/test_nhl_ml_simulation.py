import sys,unittest
sys.path.insert(0,'scripts')
from build_nhl_ml_predictions import simulate
from nhl_moneyline_model import home_moneyline_probability
class NHLMonteCarloTests(unittest.TestCase):
    def test_seed_reproducibility(self):
        self.assertEqual(simulate(3.1,2.9,123,5000),simulate(3.1,2.9,123,5000))
    def test_convergence(self):
        for away,home in [(2.5,3.2),(3,3),(4.1,2.3)]:
            p,se,n=simulate(away,home,42,20000)
            exact=home_moneyline_probability(away,home)
            self.assertLess(abs(p-exact),max(.025,5*se))
    def test_symmetry(self):
        self.assertAlmostEqual(home_moneyline_probability(3,3),.5,places=6)
if __name__=='__main__':unittest.main()
