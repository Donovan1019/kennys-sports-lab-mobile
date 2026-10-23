import unittest
from scripts.ufc_public_mirror_ingest import build,pair,secs
class Tests(unittest.TestCase):
 def test_parsers(self):
  self.assertEqual(pair("3 of 12"),(3,12));self.assertEqual(pair("---"),(0,0));self.assertEqual(secs("2:14"),134)
 def test_match(self):
  card={"fights":[{"red":"Jane Doe","blue":"Other"}]}
  d=[{"FIRST":"Jane","LAST":"Doe","URL":"http://ufcstats.com/fighter-details/abc","NICKNAME":""}]
  t=[{"FIGHTER":"Jane Doe","HEIGHT":"5' 6","WEIGHT":"125 lbs.","REACH":"66","STANCE":"Orthodox"}]
  s=[{"FIGHTER":"Jane Doe","SIG.STR.":"8 of 16","TD":"1 of 3","TOTAL STR.":"12 of 21","SUB.ATT":"1","KD":"0","CTRL":"1:05"}]
  result=build(card,d,t,s)
  self.assertEqual(result["fighters"][0]["career_round_totals"]["sig_landed"],8)
  self.assertEqual(result["fighters"][0]["career_round_totals"]["control_seconds"],65)
  self.assertFalse(result["bet_eligible"])
 def test_ambiguous(self):
  card={"fights":[{"red":"Jane Doe","blue":"Other"}]}
  d=[{"FIRST":"Jane","LAST":"Doe","URL":"one"},{"FIRST":"Jane","LAST":"Doe","URL":"two"}]
  r=build(card,d,[{"FIGHTER":"Jane Doe"}],[{"FIGHTER":"Jane Doe"}])
  self.assertEqual(r["fighters"][0]["status"],"INSUFFICIENT_OR_AMBIGUOUS")
if __name__=="__main__":unittest.main()
