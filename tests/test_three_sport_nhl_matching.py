import datetime as dt
import importlib.util
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
history=load('history',pathlib.Path('scripts/nhl_team_history.py'))
audit=load('audit',pathlib.Path('scripts/three_sport_backtest.py'))

class NHLAuditTests(unittest.TestCase):
    def test_completed_history_only(self):
        payload={'events':[{'id':'10','date':'2026-10-20T23:00Z','status':{'type':{'completed':True}},'competitions':[{'competitors':[{'team':{'displayName':'Home Team'},'score':'4'},{'team':{'displayName':'Away Team'},'score':'2'}]}]}]}
        data=history.generate(dt.datetime(2026,10,23,tzinfo=dt.timezone.utc),lambda _:payload,days=1)
        self.assertEqual(data['teams']['Home Team'][0]['scored'],4)
        self.assertEqual(data['teams']['Away Team'][0]['allowed'],4)
    def test_match_different_separator_and_kickoff(self):
        game={'completed':True,'event':'Away Team at Home Team','home':'Home Team','away':'Away Team','home_score':4,'away_score':2,'commence_time':'2026-10-23T00:00Z'}
        pred={'market':'h2h','event':'Away Team @ Home Team','selection':'Home Team','commence_time':'2026-10-23T00:15Z'}
        self.assertEqual(audit.settle_moneyline(pred,[game]),'win')
        pred['commence_time']='2026-10-26T00:15Z'
        self.assertIsNone(audit.settle_moneyline(pred,[game]))
if __name__=='__main__':unittest.main()
