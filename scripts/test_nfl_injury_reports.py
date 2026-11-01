#!/usr/bin/env python3
import unittest
from datetime import datetime,timezone
from validate_nfl_injury_reports import validate

NOW=datetime(2026,11,1,18,0,tzinfo=timezone.utc)
def report(kind="game_designation",status="questionable"):
    return {"verified":True,"event_id":"event-123","report_type":kind,"source_url":"https://www.nfl.com/injuries/","fetched_at":"2026-11-01T17:00:00Z","players":[{"name":"Test Player","team":"Test Team","status":status}]}
class InjuryValidationTests(unittest.TestCase):
    def test_designation(self):self.assertEqual(validate({"reports":[report()]},NOW),1)
    def test_inactives(self):self.assertEqual(validate({"reports":[report("official_inactives","inactive")]},NOW),1)
    def test_wrong_status(self):
        with self.assertRaises(ValueError):validate({"reports":[report("official_inactives","questionable")]},NOW)
    def test_untrusted_source(self):
        r=report();r["source_url"]="https://nfl.com.evil.test/injuries"
        with self.assertRaises(ValueError):validate({"reports":[r]},NOW)
    def test_stale(self):
        r=report();r["fetched_at"]="2026-11-01T10:00:00Z"
        with self.assertRaises(ValueError):validate({"reports":[r]},NOW)
    def test_stale_schedule(self):
        schedule={'fetched_at':'2026-11-01T09:00:00Z','odds':[{'event_id':'event-123','event':'Test Team @ Away','commence_time':'2026-11-01T20:00:00Z'}]}
        with self.assertRaisesRegex(ValueError,'Stale NFL event schedule'):validate({'reports':[report()]},NOW,schedule=schedule)
    def test_duplicate_report(self):
        with self.assertRaisesRegex(ValueError,'Duplicate report type'):validate({'reports':[report(),report()]},NOW)
    def test_duplicate_player(self):
        r=report();r['players'].append(dict(r['players'][0]))
        with self.assertRaisesRegex(ValueError,'Duplicate player status'):validate({'reports':[r]},NOW)
    def test_conflicting_events(self):
        schedule={'fetched_at':'2026-11-01T17:00:00Z','odds':[{'event_id':'event-123','event':'Test Team @ Away','commence_time':'2026-11-01T20:00:00Z'},{'event_id':'event-123','event':'Test Team @ Other','commence_time':'2026-11-01T20:00:00Z'}]}
        with self.assertRaisesRegex(ValueError,'Conflicting NFL event records'):validate({'reports':[report()]},NOW,schedule=schedule)
    def test_empty(self):
        with self.assertRaises(ValueError):validate({"reports":[]},NOW)
if __name__=="__main__":unittest.main()
