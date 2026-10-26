import unittest
from scripts.audit_nfl_sgp_walkforward import audit
class AuditTests(unittest.TestCase):
    def test_chronological_samples(self):
        games=[{"season":2025,"week":i+1,"season_type":"REG","values":{"Passing yards":100+i}} for i in range(8)]
        result=audit({"source":"nflverse-stats-player-week","players":[{"name":"Test","games":games}]})
        self.assertEqual(result["markets"]["player_pass_yds"]["samples"],3)
        self.assertEqual(result["total_samples"],3)
    def test_reject_unknown_feed(self):
        with self.assertRaises(ValueError):
            audit({"source":"unknown","players":[]})
    def test_insufficient_data(self):
        result=audit({"source":"nflverse-stats-player-week","players":[]})
        self.assertEqual(result["total_samples"],0)
        self.assertEqual(result["markets"]["player_pass_yds"]["status"],"INSUFFICIENT_DATA")
if __name__=="__main__": unittest.main()
