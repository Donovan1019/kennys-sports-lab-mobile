import sys, unittest
from datetime import datetime, timedelta, timezone
sys.path.insert(0, "scripts")
from build_market_edges import build
NOW = datetime(2026, 11, 10, 20, tzinfo=timezone.utc)
def sample(sport="NBA", market="ML"):
    return dict(sport=sport,market=market,event="A vs B",selection="A",odds=120,point=2.5,model_source="kenny_independent_simulator",model_generated_at=(NOW-timedelta(minutes=5)).isoformat(),model_probability=.55,simulations=10000,simulation_status="COMPLETE",price_verified=True,source="verified feed",data_status="VERIFIED",lineup_status="CONFIRMED",odds_timestamp=(NOW-timedelta(minutes=5)).isoformat(),start_time=(NOW+timedelta(hours=2)).isoformat())
class FeedTests(unittest.TestCase):
    def test_four_sports_three_markets(self):
        self.assertEqual(len(build([sample(s,m) for s in ("NBA","NHL","NFL","NCAAB") for m in ("ML","SPREAD","TOTAL")],NOW)["edges"]),12)
    def test_stale_odds_rejected(self):
        r=sample();r["odds_timestamp"]=(NOW-timedelta(minutes=16)).isoformat();self.assertFalse(build([r],NOW)["edges"])
    def test_no_simulation_rejected(self):
        r=sample();r["simulation_status"]="UNAVAILABLE";self.assertFalse(build([r],NOW)["edges"])
    def test_unverified_price_rejected(self):
        r=sample();r["price_verified"]=False;self.assertFalse(build([r],NOW)["edges"])
    def test_negative_ev_rejected(self):
        r=sample();r["model_probability"]=.3;self.assertFalse(build([r],NOW)["edges"])
    def test_missing_market_point_rejected(self):
        r=sample(market="SPREAD");r.pop("point");self.assertFalse(build([r],NOW)["edges"])
    def test_missing_model_provenance_rejected(self):
        r=sample();r.pop("model_source");self.assertFalse(build([r],NOW)["edges"])
    def test_unverified_lineup_rejected(self):
        r=sample();r["lineup_status"]="UNVERIFIED";self.assertFalse(build([r],NOW)["edges"])
    def test_stale_model_rejected(self):
        r=sample();r["model_generated_at"]=(NOW-timedelta(hours=2)).isoformat();self.assertFalse(build([r],NOW)["edges"])
    def test_deduplication(self):
        self.assertEqual(len(build([sample(),sample()],NOW)["edges"]),1)
    def test_future_price_rejected(self):
        r=sample();r["odds_timestamp"]=(NOW+timedelta(minutes=1)).isoformat();self.assertFalse(build([r],NOW)["edges"])
if __name__=="__main__":unittest.main()
