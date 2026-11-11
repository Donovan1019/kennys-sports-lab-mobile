import unittest
from datetime import datetime, timedelta, timezone
from scripts.join_verified_markets import join
NOW=datetime(2026,11,11,20,tzinfo=timezone.utc)
def model():
    return dict(sport="NBA",event_id="game-1",event="A vs B",market="SPREAD",selection_id="home",selection="A",point=-3.5,model_probability=.60,simulations=10000,simulation_status="COMPLETE",data_status="VERIFIED",lineup_status="CONFIRMED",model_source="kenny_independent_simulator",model_generated_at=(NOW-timedelta(minutes=5)).isoformat(),start_time=(NOW+timedelta(hours=2)).isoformat())
def quote():
    return dict(sport="NBA",event_id="game-1",market="SPREAD",selection_id="home",point=-3.5,odds=110,price_verified=True,source="verified sportsbook",odds_timestamp=(NOW-timedelta(minutes=3)).isoformat(),start_time=(NOW+timedelta(hours=2)).isoformat())
class JoinTests(unittest.TestCase):
    def test_exact_join(self):
        self.assertEqual(len(join([model()],[quote()],NOW)["edges"]),1)
    def test_mismatched_point(self):
        q=quote();q["point"]=-4.5
        self.assertFalse(join([model()],[q],NOW)["edges"])
    def test_mismatched_selection(self):
        q=quote();q["selection_id"]="away"
        self.assertFalse(join([model()],[q],NOW)["edges"])
    def test_nan_point_rejected(self):
        q=quote();q["point"]=float("nan")
        self.assertFalse(join([model()],[q],NOW)["edges"])
    def test_join_coverage(self):
        result=join([model()],[quote()],NOW)
        self.assertEqual(result["model_contracts"],1)
        self.assertEqual(result["quote_contracts"],1)
        self.assertEqual(result["matched_contracts"],1)
    def test_unverified_price(self):
        q=quote();q["price_verified"]=False
        self.assertFalse(join([model()],[q],NOW)["edges"])
    def test_unverified_lineup(self):
        m=model();m["lineup_status"]="UNVERIFIED"
        self.assertFalse(join([m],[quote()],NOW)["edges"])
    def test_different_start_time(self):
        q=quote();q["start_time"]=(NOW+timedelta(hours=3)).isoformat()
        self.assertFalse(join([model()],[q],NOW)["edges"])
    def test_research_only_rejected(self):
        m=model();m["data_status"]="research_only"
        self.assertFalse(join([m],[quote()],NOW)["edges"])
    def test_equivalent_timezone_start_matches(self):
        m=model();q=quote()
        q["start_time"]=(NOW+timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.assertEqual(len(join([m],[q],NOW)["edges"]),1)
    def test_reject_unmatched_team_name_selection(self):
        q=quote();q["selection_id"]="Different Team"
        self.assertFalse(join([model()],[q],NOW)["edges"])
    def test_reject_stale_model(self):
        m=model();m["model_generated_at"]=(NOW-timedelta(hours=2)).isoformat()
        self.assertFalse(join([m],[quote()],NOW)["edges"])
    def test_reject_stale_odds(self):
        q=quote();q["odds_timestamp"]=(NOW-timedelta(minutes=16)).isoformat()
        self.assertFalse(join([model()],[q],NOW)["edges"])
