#!/usr/bin/env python3
import unittest
from stage_nfl_espn_injuries import stage

class StagingTests(unittest.TestCase):
    def test_extracts_players_without_verified_claim(self):
        data=stage({'timestamp':'2026-11-01T12:00:00Z','injuries':[{'id':'19','displayName':'New York Giants','injuries':[{'athlete':{'id':'12','fullName':'Example Player'},'status':'Questionable','date':'2026-11-01'}]}]},'2026-11-01T12:01:00Z')
        self.assertEqual(data['teams'][0]['players'][0]['name'],'Example Player')
        self.assertEqual(data['teams'][0]['players'][0]['raw_status'],'Questionable')
        self.assertEqual(data['verified_player_reports'],0)
        self.assertEqual(data['status'],'STAGED_UNVERIFIED')
        self.assertNotIn('reports',data)
    def test_duplicate_and_incomplete_athletes(self):
        row={'athlete':{'id':'12','fullName':'Example Player'},'status':'Out'}
        data=stage({'injuries':[{'id':'19','displayName':'New York Giants','injuries':[row,row,{'athlete':{'id':'13'}}]}]},'2026-11-01T12:01:00Z')
        self.assertEqual(len(data['teams'][0]['players']),1)
    def test_numeric_athlete_id(self):
        data=stage({'injuries':[{'id':19,'displayName':'New York Giants','injuries':[{'athlete':{'id':123,'displayName':'Example Player'},'status':'Out'}]}]},'2026-11-01T12:01:00Z')
        self.assertEqual(data['teams'][0]['players'][0]['athlete_id'],'123')
    def test_rejects_empty_extraction(self):
        with self.assertRaisesRegex(ValueError,'No ESPN injury players mapped'):stage({'injuries':[]},'2026-11-01T12:01:00Z')
    def test_rejects_missing_groups(self):
        with self.assertRaises(ValueError):stage({},'2026-11-01T12:01:00Z')
if __name__=='__main__':unittest.main()
