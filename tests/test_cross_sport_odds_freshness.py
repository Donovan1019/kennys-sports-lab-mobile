import unittest
from datetime import datetime, timedelta, timezone
from scripts.fetch_odds import fresh_rows

NOW = datetime(2026, 11, 16, 12, tzinfo=timezone.utc)

def quote(**changes):
    row = {
        "bookmaker": "draftkings", "market": "h2h",
        "commence_time": (NOW + timedelta(hours=5)).isoformat(),
        "updated_at": (NOW - timedelta(minutes=5)).isoformat(),
        "price": -110,
    }
    row.update(changes)
    return row

class CrossSportQuoteFreshnessTests(unittest.TestCase):
    def test_valid_pregame_quote(self):
        self.assertEqual(len(fresh_rows([quote()], NOW)), 1)

    def test_stale_quote_rejected(self):
        self.assertEqual(fresh_rows([quote(updated_at=(NOW-timedelta(hours=9)).isoformat())], NOW), [])

    def test_future_timestamp_rejected(self):
        self.assertEqual(fresh_rows([quote(updated_at=(NOW+timedelta(minutes=5)).isoformat())], NOW), [])

    def test_started_game_rejected(self):
        self.assertEqual(fresh_rows([quote(commence_time=(NOW-timedelta(minutes=1)).isoformat())], NOW), [])

    def test_invalid_odds_and_non_provider_rejected(self):
        self.assertEqual(fresh_rows([quote(price=0), quote(price=True), quote(price=-50),
                                     quote(bookmaker="other")], NOW), [])

    def test_good_quote_survives_bad_quotes(self):
        self.assertEqual(fresh_rows([quote(price=0), quote()], NOW), [quote()])

if __name__ == "__main__":
    unittest.main()
