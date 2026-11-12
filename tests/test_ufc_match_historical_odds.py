import unittest
from scripts.ufc_match_historical_odds import match

class CrossSourceTests(unittest.TestCase):
    def setUp(self):
        self.b=[{"event_id":"UFC Test","event_date":"2024-01-01T12:00:00+00:00","fight_id":"id1","winner":"Alpha","loser":"Beta"}]
        self.o=[{"event_name":"UFC Test","event_date":"2024-01-01","winner":"Alpha","loser":"Beta","winner_decimal_odds":1.8,"loser_decimal_odds":2.1}]
        self.f=[{"event_id":"UFC Test","fight_id":"id1","winner_probability":0.6,"start_time":"2024-01-01T12:00:00+00:00"}]
    def test_exact_match(self):
        r=match(self.b,self.o,self.f,"2024-01-01T00:00:00+00:00")
        self.assertEqual(r["matched_holdout"],1)
        self.assertFalse(r["bet_eligible"])
        self.assertEqual(r["evidence_audit"]["both_verified_candidates"],0)
        self.assertFalse(r["evidence_audit"]["point_in_time_eligible"])
        self.assertEqual(r["retrospective_all_periods"]["matched_scored"],1)
        self.assertEqual(r["retrospective_all_periods"]["status"],"DESCRIPTIVE_IN_SAMPLE_ONLY")
        self.assertIsNotNone(r["market_no_vig"]["brier"])
    def test_chronological_holdout_boundary(self):
        r=match(self.b,self.o,self.f,"2024-02-01T00:00:00+00:00")
        self.assertEqual(r["matched_holdout"],0)
        self.assertEqual(r["retrospective_all_periods"]["matched_scored"],1)
    def test_mismatched_outcome(self):
        self.o[0]["winner"]="Beta"
        self.o[0]["loser"]="Alpha"
        self.assertEqual(match(self.b,self.o,self.f,"2024-01-01T00:00:00+00:00")["matched_holdout"],0)
    def test_duplicate_rejected(self):
        self.assertEqual(match(self.b,self.o*2,self.f,"2024-01-01T00:00:00+00:00")["matched_holdout"],0)
        self.assertEqual(match(self.b,self.o*2,self.f,"2024-01-01T00:00:00+00:00")["retrospective_all_periods"]["matched_scored"],0)
if __name__=="__main__":
    unittest.main()
