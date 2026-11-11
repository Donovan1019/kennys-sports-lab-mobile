import unittest
from datetime import datetime,timedelta,timezone
from scripts.normalize_sportsbook_quotes import normalize
NOW=datetime(2026,11,11,20,tzinfo=timezone.utc)
def feed():
    return {"status":"ok","source":"the-odds-api-v4","sport":"basketball_nba","fetched_at":(NOW-timedelta(minutes=3)).isoformat(),"odds":[{"event_id":"123","event":"A @ B","market":"h2h","selection":"A","price":120,"bookmaker":"fanduel","updated_at":(NOW-timedelta(minutes=2)).isoformat(),"commence_time":(NOW+timedelta(hours=2)).isoformat()}]}
class QuoteTests(unittest.TestCase):
    def test_valid_snapshot(self):
        self.assertEqual(len(normalize({"NBA":feed()},NOW)["quotes"]),1)
    def test_stale_snapshot(self):
        f=feed();f["fetched_at"]=(NOW-timedelta(minutes=16)).isoformat()
        self.assertFalse(normalize({"NBA":f},NOW)["quotes"])
    def test_stale_quote(self):
        f=feed();f["odds"][0]["updated_at"]=(NOW-timedelta(minutes=16)).isoformat()
        self.assertFalse(normalize({"NBA":f},NOW)["quotes"])
    def test_spread_without_point(self):
        f=feed();f["odds"][0]["market"]="spreads"
        self.assertFalse(normalize({"NBA":f},NOW)["quotes"])
    def test_reject_unapproved_book(self):
        f=feed();f["odds"][0]["bookmaker"]="unknown"
        self.assertFalse(normalize({"NBA":f},NOW)["quotes"])
    def test_malformed_odds_collection(self):
        f=feed();f["odds"]=None
        self.assertFalse(normalize({"NBA":f},NOW)["quotes"])
    def test_nonfinite_price_rejected(self):
        f=feed();f["odds"][0]["price"]=float("nan")
        self.assertFalse(normalize({"NBA":f},NOW)["quotes"])
