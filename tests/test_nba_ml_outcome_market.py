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

 def test_invalid_outcome_rejected(self):
  game={'id':'g1','home':'Atlanta Hawks','away':'Miami Heat','home_win':2,'date':'2026-10-28T23:00:00Z'}
  quote={'event_id':'vendor','event':'Miami Heat @ Atlanta Hawks','commence_time':game['date'],'bookmaker':'fanduel','selection':'Atlanta Hawks','price':-120,'quote_updated_at':'2026-10-28T21:59:00Z'}
  report=evaluate([{'status':'ok','captured_at':'2026-10-28T22:00:00Z','rows':[quote]}],[game])
  self.assertEqual(report['joined_selection_rows'],0)
if __name__ == '__main__':
 unittest.main()
