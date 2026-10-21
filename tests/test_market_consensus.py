import unittest
from datetime import datetime,timezone,timedelta
from scripts.market_consensus import summarize
NOW=datetime(2026,10,21,12,tzinfo=timezone.utc)
def row(book,p,age=60):
 return {"event_id":"e","away":"Away","home":"Home","bookmaker":book,"home_no_vig":p,"away_no_vig":1-p,"captured_at":(NOW-timedelta(seconds=age)).isoformat()}
class ConsensusTests(unittest.TestCase):
 def test_two_books(self):
  result=summarize({"quotes":[row("a",.6),row("b",.62)]},NOW)
  self.assertEqual(result["events_with_2plus_books"],1)
  self.assertAlmostEqual(result["events"][0]["home_consensus_no_vig"],.61)
  self.assertAlmostEqual(result["events"][0]["home_probability_range_pp"],2)
 def test_single_book_pass(self):
  self.assertEqual(summarize({"quotes":[row("a",.6)]},NOW)["events"],[])
 def test_stale_book_pass(self):
  self.assertEqual(summarize({"quotes":[row("a",.6),row("b",.62,7200)]},NOW)["events"],[])
 def test_latest_book_quote(self):
  result=summarize({"quotes":[row("a",.4,100),row("a",.6,10),row("b",.62)]},NOW)
  self.assertAlmostEqual(result["events"][0]["home_consensus_no_vig"],.61)
if __name__=="__main__":unittest.main()
