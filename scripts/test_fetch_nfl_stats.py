#!/usr/bin/env python3
"""Offline source-schema regression checks for free NFL weekly player stats."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from fetch_nfl_stats import parse

HEAD="season,week,season_type,player_id,player_display_name,recent_team,position,passing_yards,attempts,receiving_yards,receptions,rushing_yards,carries,game_id"
class WeeklyStatsTests(unittest.TestCase):
    def test_valid_named_player_and_stats(self):
        rows=parse(HEAD+"\n2026,9,REG,p1,Example Quarterback,TB,QB,240,30,0,0,8,2,2026_09_TB_CHI\n")
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["name"],"Example Quarterback")
        self.assertEqual(rows[0]["game_id"],"2026_09_TB_CHI")
        self.assertEqual(rows[0]["values"]["Passing yards"],240)
    def test_reject_missing_player_identity(self):
        self.assertEqual(parse(HEAD+"\n2026,9,REG,,Missing,TB,QB,240,30,0,0,8,2\n"),[])
    def test_reject_invalid_negative_stats(self):
        self.assertEqual(parse(HEAD+"\n2026,9,REG,p1,Example Quarterback,TB,QB,-4,30,0,0,8,2\n"),[])
    def test_reject_missing_schema(self):
        with self.assertRaises(ValueError):
            parse("season,week,player_id\n2026,9,p1\n")
if __name__=="__main__":unittest.main()
