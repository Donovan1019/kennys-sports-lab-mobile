"""Offline contract tests for SportsGameOdds v2 normalization."""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from fetch_sportsgameodds import normalize

NOW = datetime(2026, 11, 16, tzinfo=timezone.utc)


def sample():
    return {"success": True, "data": [{
        "eventID": "evt-1", "leagueID": "NBA",
        "teams": {"home": {"names": {"long": "Boston Celtics"}},
                  "away": {"names": {"long": "New York Knicks"}}},
        "status": {"startsAt": (NOW + timedelta(days=1)).isoformat(),
                   "started": False, "ended": False, "cancelled": False},
        "odds": {
            "ml-home": {"statID": "points", "periodID": "game", "betTypeID": "ml",
                        "sideID": "home", "byBookmaker": {
                            "draftkings": {"odds": "-125", "available": True, "lastUpdatedAt": NOW.isoformat()},
                            "fanduel": {"odds": "-120", "available": False, "lastUpdatedAt": NOW.isoformat()}}},
            "total-over": {"statID": "points", "periodID": "game", "betTypeID": "ou",
                           "statEntityID": "all", "sideID": "over", "byBookmaker": {
                               "fanduel": {"odds": "-110", "overUnder": "224.5",
                                           "available": True, "lastUpdatedAt": NOW.isoformat()}}},
            "consensus": {"statID": "points", "periodID": "game", "betTypeID": "ml",
                          "sideID": "away", "bookOdds": "+115"},
        },
    }]}


class TestSportsGameOdds(unittest.TestCase):
    def test_moneyline_and_total(self):
        rows = normalize(sample(), "basketball_nba", NOW)
        self.assertEqual(len(rows), 2)
        self.assertEqual({r["market"] for r in rows}, {"h2h", "totals"})
        self.assertEqual(next(r["price"] for r in rows if r["market"] == "h2h"), -125)
        self.assertEqual(next(r["point"] for r in rows if r["market"] == "totals"), 224.5)

    def test_no_consensus_or_inactive_quotes(self):
        rows = normalize(sample(), "basketball_nba", NOW)
        self.assertEqual({r["bookmaker"] for r in rows}, {"draftkings", "fanduel"})
        self.assertFalse(any(r["selection"] == "New York Knicks" for r in rows))

    def test_stale_and_started_rejected(self):
        payload = sample()
        payload["data"][0]["odds"]["ml-home"]["byBookmaker"]["draftkings"]["lastUpdatedAt"] = (NOW - timedelta(hours=9)).isoformat()
        payload["data"][0]["status"]["started"] = True
        self.assertEqual(normalize(payload, "basketball_nba", NOW), [])
        payload["data"][0]["status"]["started"] = False
        self.assertEqual(len(normalize(payload, "basketball_nba", NOW)), 1)

    def test_nhl_goals_market(self):
        payload = sample()
        payload["data"][0]["leagueID"] = "NHL"
        rows = normalize(payload, "icehockey_nhl", NOW)
        self.assertEqual(len(rows), 2)
        self.assertEqual({r["market"] for r in rows}, {"h2h", "totals"})
        self.assertEqual(normalize(payload, "basketball_nba", NOW), [])

    def test_diagnostics_are_counts_only(self):
        counts = {}
        rows = normalize(sample(), "basketball_nba", NOW, counts)
        self.assertEqual(counts["events_returned"], 1)
        self.assertEqual(counts["matching_league"], 1)
        self.assertEqual(counts["upcoming_with_teams"], 1)
        self.assertEqual(counts["matching_market"], 2)
        self.assertEqual(counts["available_book_quotes"], 2)
        self.assertEqual(counts["valid_price_quotes"], 2)
        self.assertEqual(counts["eligible_after_time_checks"], len(rows))
        self.assertTrue(all(isinstance(value, int) for value in counts.values()))

    def test_wrong_league_rejected(self):
        self.assertEqual(normalize(sample(), "icehockey_nhl", NOW), [])

    def test_invalid_response_rejected(self):
        with self.assertRaises(ValueError):
            normalize({"success": False, "data": []}, "basketball_nba", NOW)


if __name__ == "__main__":
    unittest.main()
