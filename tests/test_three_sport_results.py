import importlib.util
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
results=load('results',pathlib.Path('scripts/three_sport_results.py'))
audit=load('audit',pathlib.Path('scripts/three_sport_backtest.py'))

class SettlementTests(unittest.TestCase):
    def test_only_completed_games(self):
        payload={'events':[{'id':'1','name':'Team A at Team B','date':'2026-10-22T20:00Z','status':{'type':{'completed':True,'name':'STATUS_FINAL'}},'competitions':[{'competitors':[{'homeAway':'away','score':'100','team':{'displayName':'Team A'}},{'homeAway':'home','score':'110','team':{'displayName':'Team B'}}]}]},{'id':'2','status':{'type':{'completed':False}}}]}
        data=results.collect('NBA','2026-10-22',fetcher=lambda _:payload)
        self.assertEqual(len(data['games']),1)
        self.assertEqual(data['games'][0]['home_score'],110)
    def test_moneyline_settlement_and_guardrails(self):
        game={'completed':True,'event':'Team A at Team B','home':'Team B','away':'Team A','home_score':110,'away_score':100}
        self.assertEqual(audit.settle_moneyline({'market':'h2h','event':'Team A at Team B','selection':'Team B'},[game]),'win')
        self.assertEqual(audit.settle_moneyline({'market':'h2h','event':'Team A at Team B','selection':'Team A'},[game]),'loss')
        self.assertIsNone(audit.settle_moneyline({'market':'player_points','event':'Team A at Team B','selection':'Team B'},[game]))
        self.assertIsNone(audit.settle_moneyline({'market':'h2h','event':'Other','selection':'Team B'},[game]))
if __name__=='__main__':unittest.main()
