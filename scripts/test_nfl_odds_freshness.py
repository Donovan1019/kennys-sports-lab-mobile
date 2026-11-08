import unittest
from datetime import datetime, timezone, timedelta
from scripts.fetch_odds import validate_rows

NOW = datetime(2026, 11, 8, 13, tzinfo=timezone.utc)
def row(**kw):
    x = {"market": "h2h", "bookmaker": "draftkings", "commence_time": (NOW + timedelta(hours=5)).isoformat(),
         "updated_at": (NOW - timedelta(minutes=5)).isoformat(), "price": -110}
    x.update(kw)
    return x

class OddsFreshnessTests(unittest.TestCase):
    def test_valid_nfl_moneyline(self):
        self.assertTrue(validate_rows([row()], "americanfootball_nfl", NOW))
    def test_empty_feed(self):
        self.assertFalse(validate_rows([], "americanfootball_nfl", NOW))
    def test_stale_quotes(self):
        self.assertFalse(validate_rows([row(updated_at=(NOW - timedelta(days=7)).isoformat())], "americanfootball_nfl", NOW))
    def test_completed_game(self):
        self.assertFalse(validate_rows([row(commence_time=(NOW - timedelta(hours=1)).isoformat())], "americanfootball_nfl", NOW))
    def test_future_quote(self):
        self.assertFalse(validate_rows([row(updated_at=(NOW + timedelta(hours=1)).isoformat())], "americanfootball_nfl", NOW))
    def test_no_spread_substitution(self):
        self.assertFalse(validate_rows([row(market="spreads")], "americanfootball_nfl", NOW))
    def test_other_sports_unmodified(self):
        self.assertTrue(validate_rows([], "basketball_nba", NOW))

if __name__ == "__main__":
    unittest.main()
