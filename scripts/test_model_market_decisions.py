import unittest
from datetime import datetime, timezone, timedelta
from scripts.build_model_market_decisions import build

NOW = datetime(2026, 11, 15, 15, tzinfo=timezone.utc)
TIP = (NOW + timedelta(hours=4)).isoformat()
QUOTE = (NOW - timedelta(minutes=5)).isoformat()


def odds():
    return {"odds": [{"market": "h2h", "bookmaker": "draftkings", "event_id": "abc",
                      "event": "Away @ Home", "selection": "Home", "price": -110,
                      "commence_time": TIP, "updated_at": QUOTE}]}


class DecisionFeedTests(unittest.TestCase):
    def test_nba_validated_positive_ev(self):
        model = {"status": "validated", "calibration_passed": True,
                 "predictions": [{"event_id": "abc", "team": "Home", "win_probability": .60}]}
        result = build({"basketball_nba": (odds(), model)}, NOW)["decisions"][0]
        self.assertEqual(result["bet_status"], "BETTING_READY")
        self.assertGreater(result["expected_value"], 0)

    def test_ncaab_research_is_visible_but_not_betting_ready(self):
        model = {"status": "RESEARCH_ONLY",
                 "predictions": [{"event_id": "abc", "team": "Home", "win_probability": .60}]}
        result = build({"basketball_ncaab": (odds(), model)}, NOW)["decisions"][0]
        self.assertEqual(result["model_status"], "READY")
        self.assertEqual(result["bet_status"], "PROVISIONAL")
        self.assertNotIn("expected_value", result)

    def test_empty_feed_reports_unavailable(self):
        result = build({}, NOW)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["decisions"], [])

    def test_unavailable_odds_do_not_publish(self):
        snapshot = odds()
        snapshot["status"] = "unavailable"
        model = {"status": "validated", "calibration_passed": True,
                 "predictions": [{"event_id": "abc", "team": "Home", "win_probability": .6}]}
        self.assertEqual(build({"basketball_nba": (snapshot, model)}, NOW)["decisions"], [])

    def test_completed_games_excluded(self):
        expired = odds()
        expired["odds"][0]["commence_time"] = (NOW - timedelta(hours=1)).isoformat()
        self.assertEqual(build({"basketball_nba": (expired, {"status": "validated", "calibration_passed": True,
                         "predictions": [{"event_id": "abc", "team": "Home", "win_probability": .6}]})}, NOW)["decisions"], [])


if __name__ == "__main__":
    unittest.main()
