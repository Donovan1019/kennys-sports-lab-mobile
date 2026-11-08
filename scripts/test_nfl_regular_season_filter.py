#!/usr/bin/env python3
"""Regression checks for ESPN NFL season classification."""
import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).with_name("refresh_nfl_moneyline_inputs.py")
spec = importlib.util.spec_from_file_location("nfl_inputs", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class SeasonFilterTests(unittest.TestCase):
    def test_regular_season(self):
        self.assertTrue(mod.is_regular_season({"season": {"type": 2}}))
        self.assertTrue(mod.is_regular_season({"season": {"type": "2"}}))
    def test_preseason_and_postseason(self):
        for value in (1, 3, "1", "3"):
            self.assertFalse(mod.is_regular_season({"season": {"type": value}}))
    def test_missing_and_unknown_are_rejected(self):
        for event in ({}, {"season": {}}, {"season": {"type": "unknown"}}, {"season": None}):
            self.assertFalse(mod.is_regular_season(event))

if __name__ == "__main__":
    unittest.main()
