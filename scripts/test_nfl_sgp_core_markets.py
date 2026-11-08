#!/usr/bin/env python3
"""Offline regression tests for the scheduled NFL core-market feed."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_nfl_sgp_core_markets as collector

class FakeResponse:
    headers = {"x-requests-remaining": "42"}
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): return False

class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "core.json"
        self.old = collector.OUT
        collector.OUT = self.path
        self.addCleanup(lambda: setattr(collector, "OUT", self.old))
        self.future = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        self.past = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    def event(self, when, key="draftkings"):
        return {"id":"event-1","commence_time":when,"away_team":"Away","home_team":"Home",
                "bookmakers":[{"key":key,"markets":[
                    {"key":"h2h","last_update":self.future,"outcomes":[{"name":"Home","price":-115},{"name":"Away","price":105}]},
                    {"key":"spreads","outcomes":[{"name":"Home","point":-3.5,"price":-110}]},
                    {"key":"totals","outcomes":[{"name":"Over","point":45.5,"price":-110}]}
                ]}]}
    def test_real_core_market_rows(self):
        with patch.dict(os.environ, {"THE_ODDS_API_KEY":"offline-test"}), patch.object(collector.urllib.request, "urlopen", return_value=FakeResponse([self.event(self.future)])), patch.object(collector.json, "load", return_value=[self.event(self.future)]):
            self.assertEqual(collector.main(), 0)
        data = json.loads(self.path.read_text())
        self.assertEqual(len(data["odds"]), 4)
        self.assertEqual({x["market"] for x in data["odds"]}, {"h2h","spreads","totals"})
        self.assertTrue(all(x["event_id"]=="event-1" for x in data["odds"]))
    def test_empty_response_does_not_overwrite(self):
        self.path.write_text("keep")
        with patch.dict(os.environ, {"THE_ODDS_API_KEY":"offline-test"}), patch.object(collector.urllib.request, "urlopen", return_value=FakeResponse([])), patch.object(collector.json, "load", return_value=[]):
            self.assertEqual(collector.main(), 1)
        self.assertEqual(self.path.read_text(), "keep")
    def test_past_events_rejected(self):
        with patch.dict(os.environ, {"THE_ODDS_API_KEY":"offline-test"}), patch.object(collector.urllib.request, "urlopen", return_value=FakeResponse([self.event(self.past)])), patch.object(collector.json, "load", return_value=[self.event(self.past)]):
            self.assertEqual(collector.main(), 1)
        self.assertFalse(self.path.exists())
    def test_missing_key_no_network(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(collector.urllib.request, "urlopen") as request:
            self.assertEqual(collector.main(), 2)
            request.assert_not_called()

if __name__=="__main__": unittest.main()
