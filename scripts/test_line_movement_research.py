import unittest
from datetime import datetime, timezone
from scripts.line_movement_research import movement, settle

class MovementTest(unittest.TestCase):
    def test_pregame_and_outcome(self):
        start="2026-10-22T20:00:00+00:00"
        times=["2026-10-22T10:00:00+00:00","2026-10-22T11:00:00+00:00","2026-10-22T21:00:00+00:00"]
        ledger={"baselines":[{"event_id":"x","event_start":start,"forecast_at":times[0],"quote_at":times[0],"status":"verified_pregame_quote"}]}
        archive={"quotes":[dict(event_id="x",bookmaker="dk",home="Boston Celtics",away="Chicago Bulls",captured_at=t,home_no_vig=p) for t,p in zip(times,[.5,.6,.9])]}
        report=movement(archive,ledger,datetime(2026,10,23,tzinfo=timezone.utc))
        self.assertEqual(report["rejected_unverified_or_conflicting"],1)
        self.assertEqual(report["event_consensus"][0]["median_change_pp"],10)
        settle(report,[dict(event_id="espn1",completed=True,commence_time=start,home="Boston Celtics",away="Chicago Bulls",home_score=100,away_score=90)])
        self.assertEqual(report["outcome_audit"]["hit_rate"],1)
    def test_missing_start(self):
        self.assertEqual(movement({"quotes":[{"event_id":"x"}]})["paired_bookmaker_series"],0)

class ArchiveReplayTest(unittest.TestCase):
    def test_original_timestamp_and_pregame_pair(self):
        from scripts.line_movement_capture import historical
        from unittest.mock import patch
        from tempfile import TemporaryDirectory
        from pathlib import Path
        import json
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"snapshot.json"
            stamp="2026-10-22T10:00:00+00:00"
            rows=[dict(event_id="x",event="Chicago Bulls @ Boston Celtics",commence_time="2026-10-22T20:00:00+00:00",bookmaker="draftkings",selection=team,price=price,quote_updated_at=stamp) for team,price in [("Boston Celtics",-120),("Chicago Bulls",110)]]
            p.write_text(json.dumps(dict(status="ok",captured_at=stamp,rows=rows)))
            with patch("scripts.line_movement_capture.Path.glob",return_value=[p]):
                result=historical("basketball_nba")
            self.assertEqual(len(result),1)
            self.assertEqual(result[0]["captured_at"],stamp)
            rows[0]["quote_updated_at"]="2026-10-22T11:00:00+00:00"
            p.write_text(json.dumps(dict(status="ok",captured_at=stamp,rows=rows)))
            with patch("scripts.line_movement_capture.Path.glob",return_value=[p]):
                self.assertEqual(historical("basketball_nba"),[])

if __name__=="__main__":
    unittest.main()
