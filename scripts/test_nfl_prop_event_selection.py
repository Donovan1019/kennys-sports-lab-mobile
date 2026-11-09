#!/usr/bin/env python3
"""Offline, no-API-credit checks for upcoming NFL game selection."""
import unittest
import json
import tempfile
from pathlib import Path
from datetime import datetime,timezone,timedelta
from fetch_nfl_props import eligible_events, extract, free_plan_budget_guard, reusable_event_ids

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

class CreditBudgetTests(unittest.TestCase):
    def test_current_month_low_balance_blocks_requests(self):
        from datetime import datetime,timezone
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"props.json"
            path.write_text(json.dumps({"fetched_at":"2026-11-09T12:00:00+00:00","remaining_credits":"0"}))
            self.assertEqual(free_plan_budget_guard(datetime(2026,11,9,tzinfo=timezone.utc),path),0)
            self.assertIsNone(free_plan_budget_guard(datetime(2026,12,1,tzinfo=timezone.utc),path))
    def test_sufficient_credits_do_not_block(self):
        from datetime import datetime,timezone
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"props.json"
            path.write_text(json.dumps({"fetched_at":"2026-11-09T12:00:00+00:00","remaining_credits":"150"}))
            self.assertIsNone(free_plan_budget_guard(datetime(2026,11,9,tzinfo=timezone.utc),path))
    def test_quote_timestamp_and_identity_retained(self):
        event={"id":"test","away_team":"A","home_team":"B","commence_time":"2026-11-15T18:00:00Z"}
        payload={"bookmakers":[{"key":"draftkings","last_update":"2026-11-15T17:00:00Z","markets":[{"key":"player_pass_yds","outcomes":[{"description":"Test QB","name":"Over","point":220.5,"price":-110}]}]}]}
        rows=extract(event,payload)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["updated_at"],"2026-11-15T17:00:00Z")
        self.assertEqual(rows[0]["player"],"Test QB")

class FullSlateCacheTests(unittest.TestCase):
    def test_reuse_requires_both_books_all_markets_and_fresh_quotes(self):
        from fetch_nfl_props import MARKETS, BOOKS
        now=datetime(2026,11,9,12,tzinfo=timezone.utc)
        event={"id":"game1"}
        rows=[{"event_id":"game1","bookmaker":book,"market":market,"updated_at":"2026-11-09T11:50:00Z"} for book in BOOKS for market in MARKETS]
        self.assertEqual(reusable_event_ids([event],{"odds":rows},now),{"game1"})
        self.assertEqual(reusable_event_ids([event],{"odds":rows[:-1]},now),set())
        rows[0]["updated_at"]="2026-11-09T10:00:00Z"
        self.assertEqual(reusable_event_ids([event],{"odds":rows},now),set())
    def test_different_game_never_reused(self):
        now=datetime(2026,11,9,12,tzinfo=timezone.utc)
        self.assertEqual(reusable_event_ids([{"id":"game2"}],{"odds":[{"event_id":"game1","bookmaker":"draftkings","market":"player_pass_yds","updated_at":"2026-11-09T11:55:00Z"}]},now),set())

if __name__=="__main__":unittest.main()
