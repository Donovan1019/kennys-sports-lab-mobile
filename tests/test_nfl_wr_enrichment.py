import csv,json,pathlib,subprocess,sys,tempfile,unittest
class SupplementTests(unittest.TestCase):
 def test_exact_join_provenance_and_coverage(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);src=root/'in.json';supp=root/'snap.csv';out=root/'out.json';audit=root/'coverage.json'
   src.write_text(json.dumps({'season':2026,'games':[{'season':2026,'week':3,'team':'NYG','player_id':'gsis-1','targets':8,'offensive_snaps':None}]}))
   with supp.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['season','week','team','player_id','offensive_snaps']);w.writeheader();w.writerow({'season':2026,'week':3,'team':'NYG','player_id':'gsis-1','offensive_snaps':54})
   subprocess.run([sys.executable,'scripts/enrich_nfl_wr_opportunity.py','--input',str(src),'--supplement',str(supp),'--source','verified snaps','--output',str(out)],check=True)
   row=json.loads(out.read_text())['games'][0]
   self.assertEqual(row['offensive_snaps'],54)
   self.assertEqual(row['metric_sources']['offensive_snaps'],'verified snaps')
   subprocess.run([sys.executable,'scripts/audit_nfl_wr_coverage.py','--input',str(out),'--output',str(audit)],check=True)
   report=json.loads(audit.read_text())
   self.assertEqual(report['metrics']['offensive_snaps']['pct'],100)
   self.assertEqual(report['metrics']['routes_run']['pct'],0)
   self.assertFalse(report['fully_covered'])
 def test_mismatched_id_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);src=root/'in.json';supp=root/'snap.csv';out=root/'out.json'
   src.write_text(json.dumps({'games':[{'season':2026,'week':3,'team':'NYG','player_id':'gsis-1'}]}))
   supp.write_text('season,week,team,player_id,offensive_snaps\n2026,3,NYG,pfr-other,54\n')
   result=subprocess.run([sys.executable,'scripts/enrich_nfl_wr_opportunity.py','--input',str(src),'--supplement',str(supp),'--source','verified snaps','--output',str(out)],capture_output=True)
   self.assertNotEqual(result.returncode,0)
   self.assertFalse(out.exists())
if __name__=='__main__':unittest.main()
