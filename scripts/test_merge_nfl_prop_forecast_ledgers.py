#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from merge_nfl_prop_forecast_ledgers import merge

class MergeTests(unittest.TestCase):
    def test_union_preserves_both(self):
        a={"forecast_id":"a","line":1}
        b={"forecast_id":"b","line":2}
        self.assertEqual([x["forecast_id"] for x in merge([a],[b])["forecasts"]],["a","b"])
    def test_identical_duplicate_is_idempotent(self):
        a={"forecast_id":"a","line":1}
        self.assertEqual(len(merge([a],[dict(a)])["forecasts"]),1)
    def test_conflicting_identity_rejected(self):
        with self.assertRaises(ValueError):
            merge([{"forecast_id":"a","line":1}],[{"forecast_id":"a","line":2}])
    def test_missing_identity_rejected(self):
        with self.assertRaises(ValueError):
            merge([], [{"line":1}])
if __name__=="__main__":
    unittest.main()
