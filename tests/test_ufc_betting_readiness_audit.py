import unittest
from scripts.ufc_betting_readiness_audit import audit, quote_gate, decimal_odds

class AuditTests(unittest.TestCase):
    def test_no_betting_from_research(self):
        s={"snapshot":"2026-07-07","bet_eligible":False,"fight_history":{"rows":[]}}
        r=audit(s)
        self.assertFalse(r["bet_eligible"])
        self.assertEqual(r["matched_fights"],0)
    def test_invalid_odds_rejected(self):
        with self.assertRaises(ValueError): decimal_odds(-50)
    def test_missing_quote_data_blocked(self):
        self.assertFalse(quote_gate({"american_odds":-110})["eligible"])
    def test_verified_quote_still_requires_calibration(self):
        q={"market":"ML","selection":"fighter","american_odds":-110,
           "observed_at_utc":"2026-10-23T12:00:00Z","event_start_utc":"2026-10-24T12:00:00Z",
           "sportsbook":"test","fighter_status_verified":True,"independent_source_verified":True}
        self.assertEqual(quote_gate(q)["reason"],"MODEL_NOT_PROSPECTIVELY_CALIBRATED")

if __name__=="__main__": unittest.main()
