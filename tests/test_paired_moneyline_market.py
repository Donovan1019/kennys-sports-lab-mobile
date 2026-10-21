import unittest
from datetime import datetime,timezone,timedelta
from scripts.paired_moneyline_market import paired_moneylines
NOW=datetime(2026,10,20,22,tzinfo=timezone.utc)
def row(team,price,age=60,book="test"):
    return {"event_id":"e1","event":"Away @ Home","selection":team,"price":price,"market":"h2h","bookmaker":book,"updated_at":(NOW-timedelta(seconds=age)).isoformat(),"commence_time":(NOW+timedelta(hours=2)).isoformat()}
class PairedMoneylineTests(unittest.TestCase):
    def test_pair(self):
        rows=paired_moneylines({"odds":[row("Away",-110),row("Home",-110)]},NOW)
        self.assertEqual(len(rows),1)
        self.assertAlmostEqual(rows[0]["home_no_vig"],.5)
    def test_missing_side(self):self.assertEqual(paired_moneylines({"odds":[row("Home",-110)]},NOW),[])
    def test_stale_side(self):self.assertEqual(paired_moneylines({"odds":[row("Away",-110),row("Home",-110,1200)]},NOW),[])
    def test_cross_book_not_paired(self):self.assertEqual(paired_moneylines({"odds":[row("Away",-110),row("Home",-110,book="other")]},NOW),[])
if __name__=="__main__":unittest.main()
