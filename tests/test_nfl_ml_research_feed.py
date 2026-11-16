import unittest
from datetime import datetime, timedelta, timezone
from scripts.build_nfl_ml_predictions import build

NOW = datetime(2026, 11, 16, 18, tzinfo=timezone.utc)
def history(name):
    return {"team": name, "score_history": [
        {"date": (NOW-timedelta(days=d)).isoformat(), "scored": 28, "allowed": 20, "season_type": 2}
        for d in range(1, 6)]}

def fixture():
    event = "Away Team @ Home Team"
    odds = {"sport": "americanfootball_nfl", "status": "ok",
            "fetched_at": (NOW-timedelta(minutes=10)).isoformat(),
            "odds": [{"market": "h2h", "event_id": "sgo-42", "event": event,
                      "commence_time": (NOW+timedelta(hours=2)).isoformat(),
                      "price": -110, "selection": "Home Team"}]}
    inputs = {"source_games_fetched_at": (NOW-timedelta(hours=1)).isoformat(),
              "games": [{"event_id": "espn-other-id", "teams": [history("Home Team"), history("Away Team")]}]}
    return odds, inputs

class NFLResearchTest(unittest.TestCase):
    def test_independent_matching_ignores_provider_event_id_difference(self):
        odds, inputs = fixture()
        result = build(odds, inputs, NOW)
        self.assertEqual(result["status"], "research_only")
        self.assertEqual(len(result["predictions"]), 2)
        self.assertEqual({r["event_id"] for r in result["predictions"]}, {"sgo-42"})
        self.assertAlmostEqual(sum(r["win_probability"] for r in result["predictions"]), 1, places=5)
        self.assertFalse(result["calibration_passed"])

    def test_stale_inputs_rejected(self):
        odds, inputs = fixture()
        inputs["source_games_fetched_at"] = (NOW-timedelta(days=3)).isoformat()
        with self.assertRaises(ValueError):
            build(odds, inputs, NOW)

    def test_post_snapshot_history_not_used(self):
        odds, inputs = fixture()
        for team in inputs["games"][0]["teams"]:
            team["score_history"] = [dict(row, date=(NOW+timedelta(days=1)).isoformat()) for row in team["score_history"]]
        self.assertEqual(build(odds, inputs, NOW)["predictions"], [])

if __name__ == "__main__":
    unittest.main()
