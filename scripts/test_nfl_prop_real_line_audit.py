#!/usr/bin/env python3
"""Offline regression tests for fail-closed NFL sportsbook-line snapshot audit."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_nfl_prop_real_lines import audit

BASE = {
    "forecast_id": "a", "event_id": "game1", "market": "player_pass_yds",
    "line": 220.5, "outcome": 240, "model_probability": 0.6,
    "over_odds": -110, "under_odds": -110,
    "quoted_at": "2026-10-25T15:00:00Z",
    "forecast_at": "2026-10-25T15:05:00Z",
    "kickoff": "2026-10-25T17:00:00Z",
    "outcome_verified": True,
}

class AuditTests(unittest.TestCase):
    def test_valid_record_remains_blocked(self):
        d = audit([dict(BASE)])
        self.assertEqual(d["markets"]["player_pass_yds"]["samples"], 1)
        self.assertEqual(d["markets"]["player_pass_yds"]["model_brier"], 0.16)
        self.assertEqual(d["bet_eligibility"], "BLOCKED")
        self.assertFalse(d["markets"]["player_pass_yds"]["live_use_eligible"])

    def test_future_quote_rejected(self):
        row = dict(BASE, quoted_at="2026-10-25T15:10:00Z")
        self.assertEqual(audit([row])["exclusions"]["point_in_time_invalid"], 1)

    def test_unverified_outcome_rejected(self):
        self.assertEqual(audit([dict(BASE, outcome_verified=False)])["exclusions"]["unverified_outcome"], 1)

    def test_duplicate_forecast_not_double_counted(self):
        d = audit([dict(BASE), dict(BASE)])
        self.assertEqual(d["markets"]["player_pass_yds"]["samples"], 1)
        self.assertEqual(d["exclusions"]["duplicate"], 1)

    def test_push_excluded(self):
        d = audit([dict(BASE, outcome=220.5)])
        self.assertEqual(d["exclusions"]["push"], 1)
        self.assertFalse(d["markets"])

    def test_missing_market_prices_rejected(self):
        d = audit([dict(BASE, over_odds=None)])
        self.assertEqual(d["exclusions"]["missing_two_sided_odds"], 1)

if __name__ == "__main__":
    unittest.main()
