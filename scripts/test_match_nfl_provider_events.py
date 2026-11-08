import unittest
from scripts.match_nfl_provider_events import match

GAME = {"event_id": "espn-1", "away": "Buffalo Bills", "home": "New York Jets", "commence_time": "2026-11-09T01:00:00Z"}
def quote(event_id="odds-9", when="2026-11-09T01:00:00Z", team="Buffalo Bills"):
    return {"event_id": event_id, "commence_time": when, "market": "h2h", "bookmaker": "draftkings", "selection": team}

class ProviderCrosswalkTests(unittest.TestCase):
    def test_distinct_provider_ids_match_by_team_and_kickoff(self):
        r = match([GAME], [quote(), quote(team="New York Jets")])
        self.assertEqual(r["matched_games"], 1)
        self.assertEqual(r["matches"][0]["odds_event_id"], "odds-9")
    def test_wrong_team_rejected(self):
        self.assertEqual(match([GAME], [quote(), quote(team="Miami Dolphins")])["matched_games"], 0)
    def test_wrong_kickoff_rejected(self):
        self.assertEqual(match([GAME], [quote(when="2026-11-10T01:00:00Z"), quote(when="2026-11-10T01:00:00Z", team="New York Jets")])["matched_games"], 0)
    def test_ambiguous_matches_rejected(self):
        rows = [quote(), quote(team="New York Jets"), quote(event_id="odds-10"), quote(event_id="odds-10", team="New York Jets")]
        self.assertEqual(match([GAME], rows)["warnings"][0]["reason"], "ambiguous")
    def test_reused_bookmaker_event_rejected(self):
        r = match([GAME, dict(GAME, event_id="espn-2")], [quote(), quote(team="New York Jets")])
        self.assertEqual(r["matched_games"], 1)
        self.assertEqual(r["warnings"][0]["reason"], "sportsbook event reused")

if __name__ == "__main__":
    unittest.main()
