"""Regression: collection must not bypass verified NBA ledger admission."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import fetch_nba_nhl_props as collector


class NBACollectorLedgerIntegrity(unittest.TestCase):
    def test_raw_collection_does_not_write_verified_ledger(self):
        event = {
            "id": "future-game", "home_team": "Home", "away_team": "Away",
            "commence_time": "2099-01-01T20:00:00Z",
        }
        odds = {
            "bookmakers": [{
                "key": "fanduel", "last_update": "2026-10-28T12:00:00Z",
                "markets": [{
                    "key": "player_points",
                    "outcomes": [
                        {"description": "Example Player", "name": "Over",
                         "point": 19.5, "price": -110}
                    ],
                }],
            }]
        }
        with tempfile.TemporaryDirectory() as directory:
            original = Path.cwd()
            try:
                os.chdir(directory)
                with patch.object(collector, "get", side_effect=[([event], "200"), (odds, "199")]):
                    collector.collect("nba", 1, "test-key")
                feed = Path("feed/nba_props.json")
                self.assertTrue(feed.exists())
                self.assertEqual(len(json.loads(feed.read_text())["odds"]), 1)
                self.assertFalse(Path("feed/nba_prop_pregame_ledger.jsonl").exists(),
                                 "Raw collector must never bypass quote verification")
            finally:
                os.chdir(original)


if __name__ == "__main__":
    unittest.main()
