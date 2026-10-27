import unittest
from scripts.audit_nfl_calibration_backtest import audit

class AuditTests(unittest.TestCase):
    def test_missing_sample_size_blocks_comparison(self):
        f={"event_id":"g","player":"P","market":"player_rush_yds","forecast_at":"2026-10-25T10:00:00Z","kickoff":"2026-10-25T17:00:00Z","model_probability":0.6,"model_version":"2025-prior-season-laplace-v1","line":50.5}
        o={"event_id":"g","player":"P","market":"player_rush_yds","outcome":60,"outcome_verified":True}
        r=audit([f],[o])
        self.assertEqual(r["status"],"INSUFFICIENT_EVIDENCE")
        self.assertEqual(r["matched_forecasts_missing_source_games"],1)
        self.assertIsNone(r["revised_brier"])
    def test_two_books_one_independent_outcome(self):
        f={"event_id":"g","player":"P","market":"player_rush_yds","forecast_at":"2026-10-25T10:00:00Z","kickoff":"2026-10-25T17:00:00Z","model_probability":0.6,"source_games":8,"model_version":"2025-prior-season-laplace-v1","line":50.5}
        o={"event_id":"g","player":"P","market":"player_rush_yds","outcome":60,"outcome_verified":True}
        r=audit([f,dict(f,bookmaker="fanduel")],[o])
        self.assertEqual(r["independent_scored_markets"],1)
        self.assertEqual(r["unique_games"],1)
if __name__=="__main__":unittest.main()
