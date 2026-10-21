import math
import unittest
from scripts.matchup_monte_carlo import simulate_game, probability
from scripts.sport_simulation import simulate_sport

class CorrelatedScoreTests(unittest.TestCase):
    def test_default_unchanged(self):
        a=simulate_game(20,24,7,7,trials=1000,seed=3)
        b=simulate_game(20,24,7,7,trials=1000,seed=3,score_correlation=0)
        self.assertEqual(a,b)

    def test_positive_correlation_increases_total_variance(self):
        independent=simulate_game(80,80,10,10,trials=10000,seed=5)
        correlated=simulate_game(80,80,10,10,trials=10000,seed=5,score_correlation=.7)
        def variance(scores):
            totals=[a+h for a,h in scores]
            mean=sum(totals)/len(totals)
            return sum((x-mean)**2 for x in totals)/len(totals)
        self.assertGreater(variance(correlated),variance(independent)*1.4)

    def test_invalid_correlation_rejected(self):
        for rho in (-1,1,float('nan'),float('inf'),"0.2",True):
            with self.assertRaises(ValueError):
                simulate_game(20,24,7,7,trials=1000,score_correlation=rho)

    def test_nhl_nonzero_correlation_rejected(self):
        with self.assertRaises(ValueError):
            simulate_sport("icehockey_nhl",3,3,1,1,score_correlation=.2)

    def test_correlated_market_probabilities_are_valid(self):
        scores=simulate_sport("americanfootball_nfl",20,24,7,7,score_correlation=.25)
        r=probability(scores,"totals","over",45,"A","H")
        self.assertEqual(sum(r[k] for k in ("wins","pushes","losses")),10000)
        self.assertTrue(0<=r["probability"]<=1)

if __name__=="__main__":
    unittest.main()
