"""Regression tests for verified historical opponent identity."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

espn = load("espn_opponents", "scripts/fetch_nba_nhl_stats.py")
nhl = load("nhl_opponents", "scripts/fetch_nhl_official_stats.py")
nfl = load("nfl_opponents", "scripts/fetch_nfl_stats.py")

class OpponentIdentityTests(unittest.TestCase):
    def test_espn_opponents_from_two_team_boxscore(self):
        def team(abbr, athlete):
            return {"team":{"abbreviation":abbr},"statistics":[{"labels":["PTS"],"athletes":[{"athlete":{"id":athlete,"displayName":athlete},"stats":["12"]}]}]}
        rows = espn.parse_summary({"boxscore":{"players":[team("BOS","1"),team("NYK","2")]}},"nba","100","2026-11-06")
        self.assertEqual({r["team"]:r["opponent_abbr"] for r in rows},{"BOS":"NYK","NYK":"BOS"})

    def test_espn_no_opponent_when_only_one_team(self):
        team={"team":{"abbreviation":"BOS"},"statistics":[{"labels":["PTS"],"athletes":[{"athlete":{"id":"1","displayName":"Test"},"stats":["5"]}]}]}
        rows=espn.parse_summary({"boxscore":{"players":[team]}},"nba","100","2026-11-06")
        self.assertNotIn("opponent_abbr",rows[0])

    def test_nhl_official_opponent_from_other_side(self):
        payload={"awayTeam":{"abbrev":"NYR"},"homeTeam":{"abbrev":"BOS"},"playerByGameStats":{"awayTeam":{"forwards":[{"playerId":1,"name":{"default":"Test Player"},"goals":1,"assists":0,"sog":2}]}}}
        rows=nhl.parse_boxscore(payload,"100","2026-11-06")
        self.assertEqual(rows[0]["opponent_abbr"],"BOS")

    def test_nfl_source_opponent_optional(self):
        import io,csv
        fields=["season","week","player_id","player_display_name","recent_team","position","season_type","receptions","opponent_team"]
        buf=io.StringIO();writer=csv.DictWriter(buf,fieldnames=fields);writer.writeheader()
        writer.writerow(dict(season="2026",week="9",player_id="1",player_display_name="Test Player",recent_team="NYJ",position="WR",season_type="REG",receptions="4",opponent_team="BUF"))
        self.assertEqual(nfl.parse(buf.getvalue())[0]["opponent_abbr"],"BUF")
        fields.remove("opponent_team");buf=io.StringIO();writer=csv.DictWriter(buf,fieldnames=fields);writer.writeheader()
        writer.writerow(dict(season="2026",week="9",player_id="1",player_display_name="Test Player",recent_team="NYJ",position="WR",season_type="REG",receptions="4"))
        self.assertNotIn("opponent_abbr",nfl.parse(buf.getvalue())[0])

if __name__=="__main__":
    unittest.main()
