#!/usr/bin/env python3
"""Offline regression tests for NFL pre-kickoff snapshot archive."""
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import importlib.util

SPEC = importlib.util.spec_from_file_location("nfl_archive", Path(__file__).with_name("archive_nfl_moneyline_snapshots.py"))
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)
UTC = dt.timezone.utc


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "feed").mkdir()
        self.now = dt.datetime.now(UTC)
        self.ts = (self.now - dt.timedelta(minutes=10)).isoformat()
        self.future = (self.now + dt.timedelta(days=2)).isoformat()
        self.past = (self.now - dt.timedelta(days=3)).isoformat()
        self.patch_root = patch.object(mod, "ROOT", self.root)
        self.patch_root.start()
        self.addCleanup(self.patch_root.stop)

    def write(self, kind, payload):
        name = "independent_game_inputs.json" if kind == "inputs" else "americanfootball_nfl.json"
        (self.root / "feed" / name).write_text(json.dumps(payload))

    def test_inputs_archive(self):
        self.write("inputs", {"source_games_fetched_at": self.ts, "source": "test", "games": [
            {"commence_time": self.future, "teams": [{"score_history": [{"date": self.past, "scored": 10, "allowed": 7}]}]}]})
        mod.archive("inputs")
        files = list((self.root / "archive" / "nfl_moneyline" / "inputs").glob("*.json"))
        self.assertEqual(len(files), 1)
        self.assertEqual(len(json.loads(files[0].read_text())["games"]), 1)
        mod.archive("inputs")
        self.assertEqual(len(list(files[0].parent.glob("*.json"))), 1)

    def test_reject_future_scoring_history(self):
        self.write("inputs", {"source_games_fetched_at": self.ts, "games": [
            {"commence_time": self.future, "teams": [{"score_history": [{"date": self.future}]}]}]})
        with self.assertRaises(ValueError):
            mod.archive("inputs")

    def test_skip_stale_odds(self):
        self.write("odds", {"fetched_at": (self.now - dt.timedelta(days=2)).isoformat(), "odds": [
            {"market": "h2h", "bookmaker": "draftkings", "commence_time": self.future, "updated_at": self.ts}]})
        mod.archive("odds")
        self.assertFalse((self.root / "archive").exists())

    def test_filter_odds_to_pregame_quotes(self):
        self.write("odds", {"fetched_at": self.ts, "odds": [
            {"market": "h2h", "bookmaker": "draftkings", "commence_time": self.future, "updated_at": self.ts},
            {"market": "spreads", "bookmaker": "draftkings", "commence_time": self.future, "updated_at": self.ts},
            {"market": "h2h", "bookmaker": "other", "commence_time": self.future, "updated_at": self.ts}]})
        mod.archive("odds")
        files = list((self.root / "archive" / "nfl_moneyline" / "odds").glob("*.json"))
        self.assertEqual(len(json.loads(files[0].read_text())["odds"]), 1)


if __name__ == "__main__":
    unittest.main()
