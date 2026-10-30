import unittest
from scripts.audit_nba_ml_possession_backtest import evaluate
class TestPossessionBacktest(unittest.TestCase):
 def test_missing_history_fails_closed(self):
  r=evaluate([])
  self.assertEqual(r["status"],"insufficient_evidence")
  self.assertFalse(r["betting_eligible"])
 def test_incomplete_game_rejected(self):
  r=evaluate([{"id":"x","date":"2026-01-01T00:00:00Z","home":"A","away":"B"}])
  self.assertEqual(r["evaluated_games"],0)
if __name__=="__main__":unittest.main()
