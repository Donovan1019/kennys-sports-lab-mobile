import unittest
from scripts.audit_nfl_sgp_walkforward import audit
class AuditTests(unittest.TestCase):
    def test_chronological_samples(self):
        games=[{"season":2025,"week":i+1,"season_type":"REG","values":{"Passing yards":100+i}} for i in range(8)]
        result=audit({"source":"nflverse-stats-player-week","players":[{"name":"Test","position":"QB","games":games}]})
        self.assertEqual(result["markets"]["player_pass_yds"]["samples"],3)
        self.assertEqual(result["total_samples"],3)
    def test_position_and_zero_production_gate(self):
        games=[{"season":2025,"week":i+1,"season_type":"REG","values":{"Passing yards":0 if i==2 else 100+i}} for i in range(8)]
        data={"source":"nflverse-stats-player-week","players":[{"position":"RB","games":games}]}
        self.assertEqual(audit(data)["total_samples"],0)
        data["players"][0]["position"]="QB"
        self.assertEqual(audit(data)["total_samples"],3)
        self.assertEqual(audit(data)["integrity"]["zero_market_stat"],1)
    def test_missing_is_not_zero(self):
        games=[{"season":2025,"week":i+1,"season_type":"REG","values":({"Passing yards":0} if i==1 else {} if i==2 else {"Passing yards":100+i})} for i in range(8)]
        data={"source":"nflverse-stats-player-week","players":[{"position":"QB","games":games}]}
        result=audit(data)
        self.assertEqual(result["integrity"]["missing_market_stat"],9)
        self.assertEqual(result["integrity"]["zero_market_stat"],1)
        self.assertEqual(result["total_samples"],2)
    def test_reject_unknown_feed(self):
        with self.assertRaises(ValueError):
            audit({"source":"unknown","players":[]})
    def test_insufficient_data(self):
        result=audit({"source":"nflverse-stats-player-week","players":[]})
        self.assertEqual(result["total_samples"],0)
        self.assertEqual(result["markets"]["player_pass_yds"]["status"],"INSUFFICIENT_DATA")
if __name__=="__main__": unittest.main()
