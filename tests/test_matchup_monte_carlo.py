import unittest
from scripts.matchup_monte_carlo import simulate_game,probability,build_forecasts,probability_and_ev
class MonteCarloTests(unittest.TestCase):
 def test_reproducible(self):
  self.assertEqual(simulate_game(20,24,6,7,trials=1000,seed=1),simulate_game(20,24,6,7,trials=1000,seed=1))
 def test_moneyline(self):
  scores=[(20,17),(14,21),(24,24)]
  self.assertEqual(probability(scores,'h2h','A',None,'A','B')['wins'],1)
  self.assertEqual(probability(scores,'h2h','A',None,'A','B')['pushes'],1)
 def test_spread(self):
  scores=[(20,17),(14,21),(24,24)]
  self.assertEqual(probability(scores,'spreads','A',-3,'A','B')['pushes'],1)
 def test_total(self):
  scores=[(20,17),(14,21),(24,24)]
  self.assertEqual(probability(scores,'totals','Over',37,'A','B')['pushes'],1)
 def test_ev(self):
  self.assertAlmostEqual(probability_and_ev(.6,-110),.14545454545,places=7)
 def test_empty_input_no_forecasts(self):
  inputs={'source':'verified-independent-team-scoring','games':[]}
  odds={'source':'the-odds-api-v4','odds':[]}
  self.assertEqual(build_forecasts(inputs,odds)['predictions'],[])
 def test_invalid_distribution(self):
  with self.assertRaises(ValueError):simulate_game(20,24,0,7)
if __name__=='__main__':unittest.main()
