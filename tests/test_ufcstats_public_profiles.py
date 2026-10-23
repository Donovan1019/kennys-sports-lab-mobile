import unittest
from scripts.ufcstats_public_profiles import key,parse_directory,parse_fighter,probe
class Robots:
 def can_fetch(self,agent,url):return True
class Tests(unittest.TestCase):
 def test_names(self):
  self.assertEqual(key("José Aldo"),"jose aldo")
 def test_directory(self):
  h='<a href="http://ufcstats.com/fighter-details/0123456789abcdef">José Aldo</a>'
  self.assertEqual(len(parse_directory(h)["jose aldo"]),1)
 def test_split_first_last_name(self):
  url='http://ufcstats.com/fighter-details/0123456789abcdef'
  html='<a href="'+url+'">Alexander</a><a href="'+url+'">Volkanovski</a>'
  self.assertEqual(parse_directory(html)['alexander volkanovski'],{url})
 def test_fighter(self):
  h='<li>SLpM: 4.21</li><li>SApM: 3.12</li><li>Str. Acc.: 49%</li><li>Str. Def.: 55%</li><li>TD Avg.: 1.20</li><li>TD Acc.: 40%</li><li>TD Def.: 70%</li><li>Sub. Avg.: 0.40</li>'
  p=parse_fighter(h)
  self.assertEqual(len(p),8)
  self.assertEqual(p["sig_strike_accuracy"],.49)
 def test_fail_closed(self):
  card={"fights":[{"red":"A","blue":"B"}]}
  report=probe(card,fetch=lambda url: "",robots=Robots(),delay=0)
  self.assertFalse(report["bet_eligible"])
  self.assertEqual(len(report["fighters"]),2)
if __name__=="__main__":unittest.main()
