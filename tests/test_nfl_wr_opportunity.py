import csv,json,pathlib,subprocess,sys,tempfile,unittest
class WRFeedTest(unittest.TestCase):
 def test_verified_denominator_and_missing_charted_metrics(self):
  with tempfile.TemporaryDirectory() as td:
   inp=pathlib.Path(td)/'weekly.csv';out=pathlib.Path(td)/'out.json'
   fields=['player_id','player_name','recent_team','position','season','week','targets','receptions','receiving_yards']
   players=[('q','QB',0),('w1','WR',10),('w2','WR',5),('t','TE',3),('r','RB',2),('w3','WR',1)]
   with inp.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for name,pos,tgt in players:w.writerow(dict(player_id=name,player_name=name,recent_team='NYG',position=pos,season=2026,week=1,targets=tgt,receptions=1,receiving_yards=10))
   subprocess.run([sys.executable,'scripts/build_nfl_wr_opportunity.py','--input',str(inp),'--season','2026','--output',str(out)],check=True)
   data=json.loads(out.read_text());p=next(x for x in data['games'] if x['player_id']=='w1')
   self.assertEqual(p['team_targets'],21)
   self.assertEqual(p['targets'],10)
   self.assertIsNone(p['routes_run'])
   self.assertIsNone(p['first_read_targets'])
   self.assertIsNone(p['end_zone_targets'])
if __name__=='__main__':unittest.main()
