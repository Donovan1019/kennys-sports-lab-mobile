#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from fetch_nfl_injury_observations import parse
class InjuryObservationTests(unittest.TestCase):
 def test_reports_are_not_inactives(self):
  payload={"injuries":[{"id":"1","displayName":"Example Team","injuries":[{"athlete":{"displayName":"Example Player"},"status":"Questionable","date":"2026-11-09T12:00:00Z"}]}]}
  d=parse(payload,"2026-11-09T12:05:00Z")
  self.assertEqual(d["observed_reports"],1)
  self.assertEqual(d["verified_player_reports"],0)
  self.assertFalse(d["injuries"][0]["confirmed_inactive"])
  self.assertFalse(d["injuries"][0]["usage_adjustment_eligible"])
 def test_malformed_missing_and_naive_timestamps_rejected(self):
  d=parse({"injuries":[{"id":"1","injuries":[{"athlete":{"displayName":"A"},"status":"Out","date":"2026-11-09T12:00:00"}]}]},"now")
  self.assertEqual(d["observed_reports"],0)
  self.assertEqual(d["invalid_records"],1)
  with self.assertRaises(ValueError):parse({}, "now")
 def test_athlete_id_preserved_not_verified(self):
  payload={"injuries":[{"id":"1","displayName":"Example Team","injuries":[{"athlete":{"id":"12345","displayName":"Example Player"},"status":"Questionable","date":"2026-11-09T12:00:00Z"}]}]}
  d=parse(payload,"2026-11-09T12:05:00Z")
  self.assertEqual(d["injuries"][0]["espn_athlete_id"],"12345")
  self.assertFalse(d["injuries"][0]["usage_adjustment_eligible"])
if __name__=="__main__":unittest.main()
