import unittest
from datetime import datetime,timezone,timedelta
from scripts.archive_paired_moneylines import append_snapshot
NOW=datetime(2026,10,21,12,tzinfo=timezone.utc)
def quote(side,age=60):
    return {"event_id":"game","event":"Away @ Home","market":"h2h","bookmaker":"book","selection":side,"price":-110,"commence_time":(NOW+timedelta(hours=2)).isoformat(),"updated_at":(NOW-timedelta(seconds=age)).isoformat()}
class ArchiveTests(unittest.TestCase):
    def test_fresh_pair_archived(self):
        a=append_snapshot({"quotes":[]},{"sport":"basketball_nba","odds":[quote("Away"),quote("Home")]},NOW)
        self.assertEqual(a["added"],1)
        self.assertEqual(a["quotes"][0]["sport"],"basketball_nba")
    def test_no_stale_quotes(self):
        a=append_snapshot({"quotes":[]},{"odds":[quote("Away",1200),quote("Home")]},NOW)
        self.assertEqual(a["added"],0)
    def test_idempotent(self):
        f={"odds":[quote("Away"),quote("Home")]}
        a=append_snapshot({"quotes":[]},f,NOW)
        self.assertEqual(append_snapshot(a,f,NOW)["added"],0)
if __name__=="__main__":unittest.main()
