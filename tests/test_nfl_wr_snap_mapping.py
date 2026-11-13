import unittest
from scripts.fetch_nfl_wr_snap_counts import normalize
class SnapMappingTests(unittest.TestCase):
 def test_pfr_to_gsis(self):
  rows=[dict(season='2026',week='1',team='ARI',pfr_id='Example00',offense_snaps='43')]
  self.assertEqual(normalize(rows,2026,{'Example00':'00-1234567'})[0]['player_id'],'00-1234567')
 def test_no_crosswalk_rejected(self):
  with self.assertRaises(SystemExit):
   normalize([dict(season='2026',week='1',team='ARI',pfr_id='Example00',offense_snaps='43')],2026,{})
 def test_direct_gsis(self):
  rows=[dict(season='2026',week='1',team='ARI',gsis_id='00-1234567',offense_snaps='43')]
  self.assertEqual(len(normalize(rows,2026,{})),1)
if __name__=='__main__':unittest.main()
