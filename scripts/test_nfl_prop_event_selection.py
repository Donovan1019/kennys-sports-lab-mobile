#!/usr/bin/env python3
"""Offline, no-API-credit checks for upcoming NFL game selection."""
import unittest
from datetime import datetime,timezone,timedelta
from fetch_nfl_props import eligible_events

class EventSelectionTests(unittest.TestCase):
    def test_future_only_and_sorted(self):
        now=datetime(2026,10,25,15,0,tzinfo=timezone.utc)
        def game(name,dt):
            return {"id":name,"away_team":"Away","home_team":"Home","commence_time":dt}
        events=[
            game("past","2026-10-25T14:00:00Z"),
            game("future2","2026-10-25T20:00:00Z"),
            game("bad","invalid"),
            game("future1","2026-10-25T16:00:00Z"),
            game("naive","2026-10-25T17:00:00"),
            game("at_kickoff","2026-10-25T15:00:00Z"),
            {"id":"missing-teams","commence_time":"2026-10-25T16:00:00Z"},
        ]
        self.assertEqual([x["id"] for x in eligible_events(events,now)],["future1","future2"])
    def test_empty(self):
        self.assertEqual(eligible_events([],datetime.now(timezone.utc)),[])

if __name__=="__main__":unittest.main()
