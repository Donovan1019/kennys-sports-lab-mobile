import unittest
from scripts.ufc_market_ev import assess, no_vig_pair, implied

class MarketTests(unittest.TestCase):
    def quote(self):
        return {"event_id":"fixture","fighter":"A","opponent":"B",
                "fighter_odds":-110,"opponent_odds":-110,
                "observed_at_utc":"2026-10-23T12:00:00Z",
                "event_start_utc":"2026-10-24T12:00:00Z",
                "sportsbook":"fixture","model_probability":0.58,
                "model_calibrated":False,"fighters_verified":False,
                "source_verified":False,"odds_executable":False}
    def test_no_vig(self):
        a,b=no_vig_pair(-110,-110)
        self.assertAlmostEqual(a,0.5)
        self.assertAlmostEqual(a+b,1)
    def test_unverified_stays_blocked(self):
        x=assess(self.quote())
        self.assertFalse(x["eligible"])
        self.assertEqual(x["stake_fraction_recommended"],0)
        self.assertGreater(x["expected_roi_per_unit"],0)
    def test_verified_nonpositive_ev_blocked(self):
        q=self.quote()
        q.update({"model_probability":0.45,"model_calibrated":True,"fighters_verified":True,
                  "source_verified":True,"odds_executable":True})
        self.assertEqual(assess(q)["reason"],"NONPOSITIVE_EV")
    def test_missing_timestamp_blocked(self):
        q=self.quote()
        q["observed_at_utc"]="2026-10-25T12:00:00Z"
        self.assertEqual(assess(q)["reason"],"INVALID_INPUT")
    def test_invalid_odds_blocked(self):
        q=self.quote()
        q["fighter_odds"]=-50
        self.assertFalse(assess(q)["eligible"])

if __name__=="__main__": unittest.main()
