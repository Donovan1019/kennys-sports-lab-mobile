import unittest
from scripts.line_movement_research import movement
def quote(time,p,book="a"):
 return {"event_id":"e","bookmaker":book,"away":"Away","home":"Home","captured_at":time,"home_no_vig":p}
class MovementTests(unittest.TestCase):
 def test_requires_two_snapshots(self):
  self.assertEqual(movement({"quotes":[quote("2026-10-21T12:00:00+00:00",.5)]})["series"],[])
 def test_signed_movement(self):
  rows=[quote("2026-10-21T12:00:00+00:00",.5),quote("2026-10-21T12:10:00+00:00",.53)]
  result=movement({"quotes":rows})["series"][0]
  self.assertAlmostEqual(result["home_probability_change_pp"],3)
  self.assertFalse(result["is_verified_closing_line"])
 def test_no_cross_book_mix(self):
  rows=[quote("2026-10-21T12:00:00+00:00",.5),quote("2026-10-21T12:10:00+00:00",.53,"b")]
  self.assertEqual(movement({"quotes":rows})["series"],[])
if __name__=="__main__":unittest.main()
