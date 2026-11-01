#!/usr/bin/env python3
import unittest
from audit_nfl_espn_staging import audit
class AuditTests(unittest.TestCase):
    def test_counts_and_preserves_unverified(self):
        data={'status':'STAGED_UNVERIFIED','verified_player_reports':0,'teams':[{'espn_team_id':'19','players':[{'name':'Player A','raw_status':'Questionable','injury_date':'2026-11-01'},{'name':'Player B','raw_status':None,'injury_date':None}]}]}
        out=audit(data)
        self.assertEqual(out['players'],2)
        self.assertEqual(out['raw_status_counts'],{'MISSING':1,'Questionable':1})
        self.assertFalse(out['publication_allowed'])
    def test_rejects_verified_input(self):
        with self.assertRaises(ValueError):audit({'status':'STAGED_UNVERIFIED','verified_player_reports':1,'teams':[]})
    def test_rejects_empty(self):
        with self.assertRaises(ValueError):audit({'status':'STAGED_UNVERIFIED','verified_player_reports':0,'teams':[]})
if __name__=='__main__':unittest.main()
