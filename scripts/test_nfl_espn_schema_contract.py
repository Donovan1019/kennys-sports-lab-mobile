#!/usr/bin/env python3
"""Test the observed ESPN NFL injury schema; never infer a verified player from field names."""
import unittest
from discover_nfl_espn_injuries import inspect_payload

class DiscoveryTests(unittest.TestCase):
    def test_real_team_grouping_and_athlete_fields(self):
        sample={'injuries':[{'id':'19','displayName':'New York Giants','injuries':[{'athlete':{'id':'123','fullName':'Sample Player'},'status':'Questionable','date':'2026-11-01','type':{'name':'Injury'},'details':{}}]}]}
        result=inspect_payload(sample)
        nested=result['injury_nested_shapes']
        self.assertEqual(nested['teams_with_arrays'],1)
        self.assertIn('id',nested['all_team_keys'])
        self.assertIn('displayName',nested['all_team_keys'])
        self.assertIn('athlete',nested['all_injury_keys'])
        self.assertIn('fullName',nested['all_athlete_keys'])
        self.assertNotIn('verified_player_reports',result)
    def test_empty_injury_array_does_not_invent_player(self):
        nested=inspect_payload({'injuries':[{'id':'19','displayName':'New York Giants','injuries':[]}]})['injury_nested_shapes']
        self.assertEqual(nested['teams_with_arrays'],1)
        self.assertEqual(nested['all_injury_keys'],[])
    def test_rejects_non_object(self):
        with self.assertRaises(ValueError):inspect_payload([])
if __name__=='__main__':unittest.main()
