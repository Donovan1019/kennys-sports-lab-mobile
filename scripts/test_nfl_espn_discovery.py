#!/usr/bin/env python3
import unittest
from discover_nfl_espn_injuries import inspect_payload
class DiscoveryTests(unittest.TestCase):
    def test_detects_arrays_without_player_claims(self):
        result=inspect_payload({'injuries':[{'team':'Sample','injuries':[]}]})
        self.assertEqual(result['array_shapes']['injuries']['count'],1)
        self.assertNotIn('verified_player_reports',result)
    def test_rejects_non_object(self):
        with self.assertRaises(ValueError):inspect_payload([])
if __name__=='__main__':unittest.main()
