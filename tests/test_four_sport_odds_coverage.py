import json
import tempfile
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from scripts.four_sport_odds_coverage import audit
NOW=datetime(2026,11,11,20,tzinfo=timezone.utc)
class CoverageTests(unittest.TestCase):
    def test_missing_sports(self):
        with tempfile.TemporaryDirectory() as d:
            result=audit(Path(d),NOW)
            self.assertEqual(len(result["sports"]),4)
            self.assertTrue(all(x["status"]=="MISSING" for x in result["sports"].values()))
    def test_partial_nba(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"feed";p.mkdir()
            (p/"basketball_nba.json").write_text(json.dumps({"status":"ok","sport":"basketball_nba","fetched_at":(NOW-timedelta(minutes=2)).isoformat(),"odds":[{"event_id":"e1","market":"h2h"}]}))
            self.assertEqual(audit(Path(d),NOW)["sports"]["NBA"]["missing_markets"],["spreads","totals"])
    def test_stale(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"feed";p.mkdir()
            (p/"basketball_nba.json").write_text(json.dumps({"status":"ok","sport":"basketball_nba","fetched_at":(NOW-timedelta(minutes=30)).isoformat(),"odds":[]}))
            self.assertEqual(audit(Path(d),NOW)["sports"]["NBA"]["status"],"STALE")
