import unittest
from scripts.bridge_nfl_existing_prop_feeds import bridge
def forecast():
    return {"forecast_id":"a","event_id":"g","player":"P","market":"player_rush_yds","line":50.5,
            "model_probability":0.6,"over_odds":-110,"under_odds":-110,
            "quoted_at":"2026-10-25T12:00:00Z","forecast_at":"2026-10-25T12:01:00Z",
            "kickoff":"2026-10-25T17:00:00Z","bookmaker":"draftkings","model_version":"v1",
            "source_commit":"abc","research_only":True}
def outcome():
    return {"event_id":"g","player":"P","market":"player_rush_yds","outcome":60,
            "kickoff":"2026-10-25T17:00:00Z","verified_at":"2026-10-25T21:00:00Z",
            "outcome_verified":True,"espn_event_id":"123","source":"https://espn.com/123"}
class BridgeTests(unittest.TestCase):
    def test_grade_existing(self):
        r=bridge({"forecasts":[forecast()]},[outcome()])
        self.assertEqual(r["graded"],2)
        self.assertEqual(r["bet_eligibility"],"BLOCKED")
    def test_reject_backfilled(self):
        f=forecast();f["forecast_at"]="2026-10-25T18:00:00Z"
        self.assertEqual(bridge({"forecasts":[f]},[outcome()])["status"],"BLOCKED")
    def test_unverified_outcome_pending(self):
        o=outcome();o["outcome_verified"]=False
        self.assertEqual(bridge({"forecasts":[forecast()]},[o])["pending"],2)
if __name__=="__main__":unittest.main()
