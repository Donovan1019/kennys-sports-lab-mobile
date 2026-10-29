import unittest
from scripts.audit_nba_ml_market_evidence import audit_archives

class MarketEvidenceTests(unittest.TestCase):
 def test_pregame_coverage_never_claims_clv(self):
  row={"event_id":"game1","bookmaker":"fanduel","selection":"Atlanta Hawks","commence_time":"2026-10-29T00:00:00Z","price":-120}
  first={"status":"ok","captured_at":"2026-10-28T22:00:00Z","rows":[dict(row,quote_updated_at="2026-10-28T21:59:00Z")]}
  second={"status":"ok","captured_at":"2026-10-28T23:00:00Z","rows":[dict(row,quote_updated_at="2026-10-28T22:59:00Z",price=-130)]}
  result=audit_archives([first,second])
  self.assertEqual(result["keys_with_multiple_snapshots"],1)
  self.assertFalse(result["closing_line_value_verified"])
  self.assertFalse(result["historical_pregame_odds_backtest_verified"])
 def test_reject_post_tipoff_and_future_quotes(self):
  row={"event_id":"game1","bookmaker":"fanduel","selection":"Atlanta Hawks","commence_time":"2026-10-28T22:00:00Z","quote_updated_at":"2026-10-28T22:30:00Z","price":-120}
  result=audit_archives([{"status":"ok","captured_at":"2026-10-28T23:00:00Z","rows":[row]}])
  self.assertEqual(result["valid_quote_keys"],0)
  self.assertEqual(result["rejected_rows"],1)
if __name__=="__main__":unittest.main()
