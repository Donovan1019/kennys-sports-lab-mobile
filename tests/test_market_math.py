import unittest
from scripts.market_math import (
    implied_probability,net_profit_per_unit,expected_value,
    paired_two_way_no_vig,best_prices,fair_american
)
class TestMarketMath(unittest.TestCase):
    def test_implied(self):
        self.assertAlmostEqual(implied_probability(-110),110/210)
        self.assertAlmostEqual(implied_probability(150),100/250)
    def test_invalid(self):
        for value in (0,99,-99):
            with self.assertRaises(ValueError):implied_probability(value)
    def test_ev(self):
        self.assertAlmostEqual(expected_value(100,.5),0)
        self.assertAlmostEqual(expected_value(-110,.55),.55*100/110-.45)
        with self.assertRaises(ValueError):expected_value(-110,1.2)
    def test_no_vig(self):
        a,b=paired_two_way_no_vig(-110,-110)
        self.assertAlmostEqual(a,.5)
        self.assertAlmostEqual(a+b,1)
    def test_fair_odds(self):
        self.assertEqual(fair_american(.5),-100)
        self.assertEqual(fair_american(.4),150)
    def test_best_price(self):
        base={"event_id":"1","market":"h2h","selection":"A","point":None,"description":None}
        rows=[dict(base,bookmaker="fanduel",price=-110),dict(base,bookmaker="draftkings",price=-105)]
        self.assertEqual(next(iter(best_prices(rows).values()))["bookmaker"],"draftkings")
    def test_point_separation(self):
        base={"event_id":"1","market":"spreads","selection":"A","description":None,"price":-110}
        rows=[dict(base,bookmaker="fanduel",point=-3.5),dict(base,bookmaker="draftkings",point=-2.5)]
        self.assertEqual(len(best_prices(rows)),2)
if __name__=="__main__":unittest.main()
