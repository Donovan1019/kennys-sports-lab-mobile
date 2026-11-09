#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_nfl_prop_archive_health import inspect
class ArchiveHealthTests(unittest.TestCase):
    def test_empty_archive_is_blocked(self):
        d=inspect({"forecasts":[]},[],{"status":"PARTIAL","captured_events":0})
        self.assertEqual(d["pregame_forecasts_archived"],0)
        self.assertEqual(d["bet_eligibility"],"BLOCKED")
    def test_awaiting_grade(self):
        d=inspect({"forecasts":[{"forecast_id":"a","market":"player_pass_yds"}]},[],{})
        self.assertEqual(d["archived_forecasts_awaiting_verified_grade"],1)
    def test_duplicate_id_rejected(self):
        with self.assertRaises(ValueError):
            inspect({"forecasts":[{"forecast_id":"a"},{"forecast_id":"a"}]},[],{})
    def test_missing_schema_rejected(self):
        with self.assertRaises(ValueError):
            inspect({},[],{})
if __name__=="__main__":unittest.main()
