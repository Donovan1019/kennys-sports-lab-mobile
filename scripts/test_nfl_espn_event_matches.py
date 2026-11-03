#!/usr/bin/env python3
import unittest
from datetime import datetime,timezone
from audit_nfl_espn_event_matches import match
NOW=datetime(2026,11,1,18,tzinfo=timezone.utc)
def staging(name='New York Giants'):
    return {'status':'STAGED_UNVERIFIED','verified_player_reports':0,'fetched_at':'2026-11-01T17:00:00Z','teams':[{'espn_team_id':'19','team_name':name,'players':[{'name':'Test'}]}]}
def schedule():
    return {'fetched_at':'2026-11-01T17:00:00Z','odds':[{'event_id':'abc','event':'New York Giants @ Dallas Cowboys','commence_time':'2026-11-02T18:00:00Z'}]}
class MatchTests(unittest.TestCase):
    def test_exact_name_match_unverified(self):
        result=match(staging(),schedule(),NOW)
        self.assertEqual(result['matched_teams'],1)
        self.assertEqual(result['matched_staged_players_unverified'],1)
        self.assertEqual(result['unmatched_staged_players'],0)
        self.assertFalse(result['publication_allowed'])
        self.assertEqual(result['team_matches'][0]['candidate_event_ids'],['abc'])
    def test_no_guessing_abbreviation(self):
        result=match(staging('NY Giants'),schedule(),NOW)
        self.assertEqual(result['unmatched_teams'],1)
        self.assertEqual(result['unmatched_staged_players'],1)
    def test_stale_schedule_rejected(self):
        s=schedule();s['fetched_at']='2026-11-01T08:00:00Z'
        with self.assertRaises(ValueError):match(staging(),s,NOW)
    def test_unverified_never_published(self):
        result=match(staging(),schedule(),NOW)
        self.assertEqual(result['verified_player_reports'],0)
        self.assertEqual(result['projection_impact'],'NOT_APPLIED')
    def test_past_kickoff_cannot_match(self):
        s=schedule();s['odds'][0]['commence_time']='2026-11-01T17:30:00Z'
        with self.assertRaisesRegex(ValueError,'No NFL events'):match(staging(),s,NOW)
    def test_missing_kickoff_cannot_match(self):
        s=schedule();s['odds'][0].pop('commence_time')
        with self.assertRaisesRegex(ValueError,'No NFL events'):match(staging(),s,NOW)
    def test_same_event_id_conflicting_kickoff_rejected(self):
        s=schedule();s['odds'].append(dict(s['odds'][0],commence_time='2026-11-02T19:00:00Z'))
        with self.assertRaisesRegex(ValueError,'Conflicting schedule event'):match(staging(),s,NOW)
    def test_duplicate_same_event_and_kickoff_allowed(self):
        s=schedule();s['odds'].append(dict(s['odds'][0]))
        self.assertEqual(match(staging(),s,NOW)['schedule_event_count'],1)
    def test_ambiguous_double_header(self):
        s=schedule();s['odds'].append({'event_id':'xyz','event':'New York Giants @ Philadelphia Eagles','commence_time':'2026-11-03T18:00:00Z'})
        result=match(staging(),s,NOW)
        self.assertEqual(result['ambiguous_teams'],1)
        self.assertEqual(result['ambiguous_staged_players'],1)
if __name__=='__main__':unittest.main()
