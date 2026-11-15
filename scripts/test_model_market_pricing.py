import unittest
from datetime import datetime, timezone, timedelta
from scripts.model_market_pricing import decimal_odds, implied_probability, no_vig_probabilities, expected_value, evaluate


NOW = datetime(2026, 11, 15, 15, tzinfo=timezone.utc)
STAMP = (NOW - timedelta(minutes=5)).isoformat()


class MarketPricingTests(unittest.TestCase):
    def test_american_odds_and_break_even(self):
        self.assertAlmostEqual(decimal_odds(-110), 1.909090909, places=7)
        self.assertAlmostEqual(implied_probability(150), .4)

    def test_no_vig_removes_overround(self):
        fair = no_vig_probabilities([-110, -110])
        self.assertEqual(len(fair), 2)
        self.assertAlmostEqual(sum(fair), 1)
        self.assertAlmostEqual(fair[0], .5)

    def test_positive_ev_ready(self):
        r = evaluate(.60, -110, independent_model=True, model_verified=True,
                     event_verified=True, price_verified=True, odds_timestamp=STAMP, now=NOW)
        self.assertEqual(r["model_status"], "READY")
        self.assertEqual(r["bet_status"], "BETTING_READY")
        self.assertGreater(r["expected_value"], 0)

    def test_projection_survives_stale_odds(self):
        r = evaluate(.60, -110, independent_model=True, model_verified=True,
                     event_verified=True, price_verified=True,
                     odds_timestamp=(NOW - timedelta(hours=2)).isoformat(), now=NOW)
        self.assertEqual(r["model_status"], "READY")
        self.assertEqual(r["bet_status"], "PROVISIONAL")
        self.assertNotIn("expected_value", r)

    def test_negative_ev_not_ready(self):
        r = evaluate(.45, -110, independent_model=True, model_verified=True,
                     event_verified=True, price_verified=True, odds_timestamp=STAMP, now=NOW)
        self.assertEqual(r["bet_status"], "NO_VALUE")

    def test_market_implied_not_independent(self):
        r = evaluate(.60, -110, independent_model=False, model_verified=True,
                     event_verified=True, price_verified=True, odds_timestamp=STAMP, now=NOW)
        self.assertEqual(r["bet_status"], "BLOCKED")

    def test_invalid_prices_fail_closed(self):
        for odds in [0, 99, -99, float("nan")]:
            r = evaluate(.6, odds, independent_model=True, model_verified=True,
                         event_verified=True, price_verified=True, odds_timestamp=STAMP, now=NOW)
            self.assertEqual(r["bet_status"], "PROVISIONAL")

    def test_event_unverified_does_not_claim_ev(self):
        r = evaluate(.6, -110, independent_model=True, model_verified=True,
                     event_verified=False, price_verified=True, odds_timestamp=STAMP, now=NOW)
        self.assertEqual(r["bet_status"], "PROVISIONAL")
        self.assertNotIn("expected_value", r)


if __name__ == "__main__":
    unittest.main()
