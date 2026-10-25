#!/usr/bin/env python3
"""Offline regression tests: NFL box-score extraction and fail-closed stat mapping."""
import unittest
from import_nfl_verified_player_outcomes import extract,parse_stat
class Tests(unittest.TestCase):
 def test_exact_stat_category(self):
  sample={"boxscore":{"players":[{"statistics":[
   {"name":"passing","labels":["C/ATT","YDS","TD"],"athletes":[{"athlete":{"displayName":"Sample QB"},"stats":["20/30","275","2"]}]},
   {"name":"rushing","labels":["CAR","YDS","TD"],"athletes":[{"athlete":{"displayName":"Sample QB"},"stats":["4","19","0"]}]},
   {"name":"receiving","labels":["REC","YDS","TD"],"athletes":[{"athlete":{"displayName":"Sample WR"},"stats":["7","88","1"]}]}]}]}}
  data=extract(sample)
  self.assertEqual(parse_stat(data["sample qb"],"player_pass_yds"),275)
  self.assertEqual(parse_stat(data["sample qb"],"player_pass_tds"),2)
  self.assertEqual(parse_stat(data["sample qb"],"player_rush_yds"),19)
  self.assertEqual(parse_stat(data["sample wr"],"player_receptions"),7)
  self.assertEqual(parse_stat(data["sample wr"],"player_reception_yds"),88)
  self.assertIsNone(parse_stat(data["sample wr"],"player_pass_yds"))
 def test_ambiguous_rows_fail_closed(self):
  rows=[{"category":"receiving","values":{"YDS":"60"}},{"category":"receiving","values":{"YDS":"80"}}]
  self.assertIsNone(parse_stat(rows,"player_reception_yds"))
if __name__=="__main__":unittest.main()
