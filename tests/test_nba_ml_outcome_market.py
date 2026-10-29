import unittest
from scripts.audit_nba_ml_outcome_market import evaluate, implied

class OutcomeAuditTests(unittest.TestCase):
 def test_odds_conversion(self):
  self.assertAlmostEqual(implied(-150), 0.6)
  self.assertAlmostEqual(implied(150), 0.4)
 def test_no_data_never_approves(self):
  report=evaluate([], [])
  self.assertEqual(report['joined_selection_rows'], 0)
  self.assertFalse(report['closing_line_value_verified'])

if __name__ == '__main__':
 unittest.main()
