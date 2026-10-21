import unittest
from scripts.refresh_recent_results import merge
class RefreshTests(unittest.TestCase):
 def test_preserves_history_and_updates_existing(self):
  a={"date":"2026-10-20T23:00:00Z","away":"A","home":"H","away_score":1,"home_score":2}
  b=dict(a,home_score=3)
  c=dict(a,date="2026-10-19T23:00:00Z")
  result=merge([a,c],[b])
  self.assertEqual(len(result),2)
  self.assertEqual(result[-1]["home_score"],3)
 def test_rejects_missing_scores(self):
  self.assertEqual(merge([],[{"date":"2026-10-20","away":"A","home":"H"}]),[])
if __name__=="__main__":unittest.main()
