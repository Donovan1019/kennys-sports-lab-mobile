#!/usr/bin/env python3
import unittest
from datetime import datetime,timezone
from audit_nfl_espn_event_matches import match
NOW=datetime(2026,11,1,18,tzinfo=timezone.utc)
def staging(name='New York Giants'):
    return {'status':'STAGED_UNVERIFIED','verified_player_reports':0,'fetched_at':'2026-11-01T17:00:00Z','teams':[{'espn_team_id':'19','team_name':name,'players':[{'name':'Test'}]}]}
def schedule():
    return {'fetched_at':'2026-11-01T17:00:00Z','odds':[{'event_id':'abc','event':'New York Giants @ Dallas Cowboys'}]}
class MatchTests(unittest.TestCase):
    def test_exact_name_match_unverified(self):
        result=match(staging(),schedule(),NOW)
        self.assertEqual(result['matched_teams'],1)
        self.assertFalse(result['publication_allowed'])
        self.assertEqual(result['team_matches'][0]['candidate_event_ids'],['abc'])
    def test_no_guessing_abbreviation(self):
        self.assertEqual(match(staging('NY Giants'),schedule(),NOW)['unmatched_teams'],1)
    def test_stale_schedule_rejected(self):
        s=schedule();s['fetched_at']='2026-11-01T08:00:00Z'
        with self.assertRaises(ValueError):match(staging(),s,NOW)
    def test_unverified_never_published(self):
        result=match(staging(),schedule(),NOW)
        self.assertEqual(result['verified_player_reports'],0)
        self.assertEqual(result['projection_impact'],'NOT_APPLIED')
    def test_ambiguous_double_header(self):
        s=schedule();s['odds'].append({'event_id':'xyz','event':'New York Giants @ Philadelphia Eagles'})
        self.assertEqual(match(staging(),s,NOW)['ambiguous_teams'],1)
if __name__=='__main__':unittest.main()
