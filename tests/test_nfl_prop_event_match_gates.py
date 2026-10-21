import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from scripts.player_recommendation_readiness import inspect_nfl_quote_archive

class PropEventMatchTests(unittest.TestCase):
    def test_event_match_is_not_roster_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            event={"event_id":"e1","event":"A @ B","commence_time":"2026-10-23T00:15:00Z"}
            market={"odds":[dict(event,bookmaker="book",market="player_pass_yds",
                                 player="Player One",price=-110,
                                 updated_at="2026-10-21T14:00:00Z"),
                             dict(event,bookmaker="book",market="player_pass_yds",
                                 player="Player Two",price=-120,
                                 updated_at="2026-10-21T14:00:00Z")]}
            events={"odds":[dict(event,bookmaker="book",market="h2h",
                                 selection="A",price=-110,updated_at="2026-10-21T14:00:00Z")]}
            pp=root/"props.json"
            ep=root/"events.json"
            pp.write_text(json.dumps(market))
            ep.write_text(json.dumps(events))
            report=inspect_nfl_quote_archive(pp,ep,datetime(2026,10,21,14,30,tzinfo=timezone.utc))
            self.assertEqual(report["matched_archived_event_rows"],2)
            self.assertEqual(report["unmatched_archived_event_rows"],0)
            self.assertEqual(report["verified_player_team_assignments"],0)
            self.assertEqual(report["unverified_player_team_assignments"],2)
            self.assertEqual(report["fresh_quotes"],2)

    def test_conflicting_or_missing_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            row={"event_id":"e1","event":"A @ B","commence_time":"2026-10-23T00:15:00Z",
                 "bookmaker":"book","market":"player_receptions","player":"Player One",
                 "price":-110,"updated_at":"2026-10-21T14:00:00Z"}
            pp=root/"props.json"
            ep=root/"events.json"
            pp.write_text(json.dumps({"odds":[row,dict(row,event_id="e2")]}))
            ep.write_text(json.dumps({"odds":[dict(row,event="C @ D")]}))
            report=inspect_nfl_quote_archive(pp,ep,datetime(2026,10,21,14,30,tzinfo=timezone.utc))
            self.assertEqual(report["conflicting_archived_event_rows"],1)
            self.assertEqual(report["unmatched_archived_event_rows"],1)
            self.assertEqual(report["verified_player_team_assignments"],0)

if __name__=="__main__":
    unittest.main()
