import datetime as dt
import unittest
from scripts.fetch_nfl_oddspapi import normalize

NOW = dt.datetime(2026, 11, 8, 16, 0, tzinfo=dt.timezone.utc)
FIXTURE = {"fixtureId": "id123", "startTime": "2026-11-08T21:00:00Z", "participant1Name": "Home", "participant2Name": "Away"}
def selection(side, price, updated="2026-11-08T15:59:00Z"):
    return {"players": {"0": {"active": True, "bookmakerOutcomeId": side, "priceAmerican": price, "changedAt": updated}}}
def board(home="home", away="away", updated="2026-11-08T15:59:00Z"):
    outcomes = {
        "a": selection(home, "-110", updated),
        "b": selection(away, "+100", updated),
    }
    market = {"marketActive": True, "outcomes": outcomes}
    bookmaker = {"bookmakerIsActive": True, "markets": {"141": market}}
    return {"bookmakerOdds": {"draftkings": bookmaker}}
class OddsPapiNormalizationTests(unittest.TestCase):
    def test_explicit_sides(self):
        rows = normalize(FIXTURE, board(), NOW)
        self.assertEqual(len(rows), 2)
        self.assertEqual({r["selection"] for r in rows}, {"Home", "Away"})
    def test_opaque_outcome_ids_rejected(self):
        self.assertEqual(normalize(FIXTURE, board("141", "142"), NOW), [])
    def test_stale_rejected(self):
        self.assertEqual(normalize(FIXTURE, board(updated="2026-11-07T15:59:00Z"), NOW), [])
    def test_incomplete_two_sided_market_rejected(self):
        self.assertEqual(normalize(FIXTURE, board(away="unknown"), NOW), [])
    def test_finished_game_rejected(self):
        self.assertEqual(normalize(dict(FIXTURE, startTime="2026-11-08T15:00:00Z"), board(), NOW), [])
if __name__ == "__main__":
    unittest.main()
