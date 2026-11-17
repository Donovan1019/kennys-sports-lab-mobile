import datetime as dt
import unittest
from scripts.audit_nba_ml_outcome_market import evaluate

class OpeningWindowTests(unittest.TestCase):
    def test_opening_uses_earliest_pregame_quote_not_only_last_15_minutes(self):
        tip=dt.datetime(2026,11,10,23,0,tzinfo=dt.timezone.utc)
        def archive(hours_before,price):
            captured=tip-dt.timedelta(hours=hours_before)
            return {"status":"ok","captured_at":captured.isoformat(),"rows":[{
                "event":"Away @ Home","event_id":"source1","commence_time":tip.isoformat(),
                "quote_updated_at":captured.isoformat(),"bookmaker":"fanduel",
                "selection":"Home","price":price,"model_probability":0.8
            }]}
        game={"id":"game1","date":tip.isoformat(),"home":"Home","away":"Away","home_win":1}
        report=evaluate([archive(5,-150),archive(0.1,-180)],[game])
        self.assertEqual(report["joined_selection_rows"],1)
        self.assertEqual(report["opening_quotes_over_1h_before_tip"],1)
        self.assertEqual(report["near_tipoff_paired_rows"],1)
        self.assertAlmostEqual(report["sample_rows"][0]["opening_quote_hours_before_tip"],5)
        self.assertEqual(report["sample_rows"][0]["opening_reference_price"],-150)
        self.assertTrue(report["sample_rows"][0]["verified_near_tipoff_quote"])

if __name__=="__main__":
    unittest.main()
