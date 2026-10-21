import unittest
from scripts.nhl_moneyline_model import home_moneyline_probability
class NhlMoneylineTests(unittest.TestCase):
    def test_equal(self):self.assertAlmostEqual(home_moneyline_probability(3,3),.5,places=5)
    def test_monotonic(self):self.assertGreater(home_moneyline_probability(2.5,3.5),.5)
    def test_symmetry(self):
        self.assertAlmostEqual(home_moneyline_probability(2.3,3.1)+home_moneyline_probability(3.1,2.3),1,places=6)
    def test_invalid(self):
        with self.assertRaises(ValueError):home_moneyline_probability(0,3)
if __name__=="__main__":unittest.main()
