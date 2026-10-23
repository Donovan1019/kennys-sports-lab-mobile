import unittest
from scripts.ufc_odds_connector import normalize

class OddsConnectorTests(unittest.TestCase):
    def snapshot(self):
        return {"schema":1,"sport":"UFC","source":"fixture","source_authorized":True,
                "captured_at_utc":"2026-10-23T12:00:00Z",
                "moneylines":[{"event_id":"fight1","fighter":"A","opponent":"B",
                "fighter_odds":-110,"opponent_odds":-110,"event_start_utc":"2026-10-24T12:00:00Z",
                "sportsbook":"fixture"}]}
    def test_missing_model_probability_blocks(self):
        r=normalize(self.snapshot())
        self.assertEqual(r["markets"][0]["reason"],"MISSING_INDEPENDENT_MODEL_PROBABILITY")
        self.assertFalse(r["bet_eligible"])
    def test_unauthorized_source_rejected(self):
        s=self.snapshot()
        s["source_authorized"]=False
        with self.assertRaises(ValueError): normalize(s)
    def test_model_unverified_stays_blocked(self):
        s=self.snapshot()
        s["moneylines"][0]["model_probability"]=0.58
        r=normalize(s)
        self.assertFalse(r["markets"][0]["eligible"])
        self.assertEqual(r["markets"][0]["reason"],"VERIFICATION_OR_CALIBRATION_INCOMPLETE")
    def test_duplicate_market_blocked(self):
        s=self.snapshot()
        s["moneylines"].append(dict(s["moneylines"][0]))
        r=normalize(s)
        self.assertEqual(r["markets"][1]["reason"],"INVALID_QUOTE")
    def test_post_event_blocked(self):
        s=self.snapshot()
        s["captured_at_utc"]="2026-10-25T12:00:00Z"
        self.assertEqual(normalize(s)["markets"][0]["reason"],"INVALID_QUOTE")
if __name__=="__main__": unittest.main()
