import datetime as dt
import unittest
from scripts.ufc_odds_ev import evaluate,implied
NOW=dt.datetime(2026,10,23,12,tzinfo=dt.timezone.utc)
def market():
    return {"fight_id":"1","market":"moneyline","start_time":"2026-10-24T20:00:00Z",
            "quoted_at":"2026-10-23T11:55:00Z","red_odds":-110,"blue_odds":-110,"source":"test"}
def model():
    return {"fight_id":"1","red_win_probability":.55,"calibrated":False,"independent_holdout_passed":False}
class UFCOddsEVTests(unittest.TestCase):
    def test_no_vig_sums_to_one_and_ev(self):
        result=evaluate(market(),model(),NOW)
        self.assertAlmostEqual(sum(v["no_vig"] for v in result["sides"].values()),1)
        self.assertGreater(result["sides"]["red"]["ev_per_unit"],0)
        self.assertFalse(result["bet_eligible"])
    def test_stale_and_future_quotes_rejected(self):
        stale=market();stale["quoted_at"]="2026-10-23T10:00:00Z"
        with self.assertRaises(ValueError):evaluate(stale,model(),NOW)
        future=market();future["quoted_at"]="2026-10-23T12:05:00Z"
        with self.assertRaises(ValueError):evaluate(future,model(),NOW)
    def test_mismatched_fights_rejected(self):
        other=model();other["fight_id"]="2"
        with self.assertRaises(ValueError):evaluate(market(),other,NOW)
    def test_invalid_odds_rejected(self):
        for bad in (0,-99,99,True):
            with self.assertRaises(ValueError):implied(bad)
if __name__=="__main__":unittest.main()
