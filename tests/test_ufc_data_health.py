import unittest
from scripts.ufc_data_health import audit
def row():
    return {"event_id":"e","fight_id":"f","winner":"A","loser":"B",
            "event_date":"2026-10-01T00:00:00Z","winner_verified":True}
class UFCDataHealthTests(unittest.TestCase):
    def test_empty_dataset_is_blocked(self):
        r=audit({"results":[],"successful_days":[],"failed_days":[]},
                {"historical_bouts_used":0,"bet_eligible":False},
                {"holdout_n":0,"bet_eligible":False})
        self.assertIn("NO_VERIFIED_HISTORICAL_FIGHTS",r["blockers"])
        self.assertFalse(r["bet_eligible"])
    def test_valid_data_still_requires_independent_approval(self):
        r=audit({"results":[row()],"successful_days":["2026-10-01"],"failed_days":[]},
                {"historical_bouts_used":1,"bet_eligible":False},
                {"holdout_n":100,"bet_eligible":False})
        self.assertEqual(r["verified_fights"],1)
        self.assertIn("NO_INDEPENDENT_PRICE_AND_CALIBRATION_APPROVAL",r["blockers"])
    def test_duplicate_and_mismatch_detected(self):
        r=audit({"results":[row(),row()],"successful_days":["2026-10-01"],"failed_days":[]},
                {"historical_bouts_used":2,"bet_eligible":False},
                {"holdout_n":0,"bet_eligible":False})
        self.assertIn("INVALID_OR_DUPLICATE_HISTORICAL_ROWS",r["blockers"])
        self.assertIn("ELO_HISTORY_MISMATCH",r["blockers"])
if __name__=="__main__":unittest.main()
