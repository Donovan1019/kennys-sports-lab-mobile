import unittest
from scripts.audit_nfl_sgp_walkforward import audit
class AuditTests(unittest.TestCase):
    def test_chronological_samples(self):
        games=[{"season":2025,"week":i+1,"season_type":"REG","values":{"Passing yards":100+i,"Pass Attempts":20}} for i in range(8)]
        result=audit({"source":"nflverse-stats-player-week","players":[{"name":"Test","position":"QB","games":games}]})
        self.assertEqual(result["markets"]["player_pass_yds"]["samples"],3)
        self.assertEqual(result["total_samples"],3)
    def test_position_and_zero_production_gate(self):
        games=[{"season":2025,"week":i+1,"season_type":"REG","values":{"Passing yards":0 if i==2 else 100+i,"Pass Attempts":20}} for i in range(8)]
        data={"source":"nflverse-stats-player-week","players":[{"position":"RB","games":games}]}
        self.assertEqual(audit(data)["total_samples"],0)
        data["players"][0]["position"]="QB"
        self.assertEqual(audit(data)["total_samples"],3)
        self.assertEqual(audit(data)["integrity"]["zero_market_stat"],1)
    def test_missing_is_not_zero(self):
        games=[{"season":2025,"week":i+1,"season_type":"REG","values":({"Passing yards":0,"Pass Attempts":20} if i==1 else {"Pass Attempts":20} if i==2 else {"Passing yards":100+i,"Pass Attempts":20})} for i in range(8)]
        data={"source":"nflverse-stats-player-week","players":[{"position":"QB","games":games}]}
        result=audit(data)
        self.assertEqual(result["integrity"]["missing_market_stat"],9)
        self.assertEqual(result["integrity"]["zero_market_stat"],1)
        self.assertEqual(result["total_samples"],2)
    def test_opportunity_gate_retains_real_zero(self):
        games=[{"season":2025,"week":i+1,"season_type":"REG","values":{"Receptions":0 if i==5 else 3,"Targets":0 if i==6 else 4}} for i in range(8)]
        result=audit({"source":"nflverse-stats-player-week","players":[{"position":"WR","games":games}]})
        self.assertEqual(result["markets"]["player_receptions"]["samples"],2)
        self.assertEqual(result["opportunity"]["zero_opportunity"],1)
        self.assertEqual(result["participation_status"],"OPPORTUNITY_CONFIRMED_ONLY")
    def test_missing_opportunity_excluded(self):
        games=[{"season":2025,"week":i+1,"season_type":"REG","values":{"Passing yards":100+i}} for i in range(8)]
        result=audit({"source":"nflverse-stats-player-week","players":[{"position":"QB","games":games}]})
        self.assertEqual(result["total_samples"],0)
        self.assertEqual(result["opportunity"]["unverified"],8)
    def test_baseline_diagnostic(self):
        games=[{"season":2025,"week":i+1,"season_type":"REG","values":{"Passing yards":100+i,"Pass Attempts":20}} for i in range(8)]
        result=audit({"source":"nflverse-stats-player-week","players":[{"position":"QB","games":games}]})
        market=result["markets"]["player_pass_yds"]
        self.assertIn("chronological_rolling_brier",market)
        self.assertIn("skill_vs_chronological_rolling",market)
        self.assertIn("constant_rate_brier_in_sample",market)
        self.assertIn("skill_vs_in_sample_constant",market)
        self.assertIn("look-ahead",result["baseline_warning"])
    def test_chronological_baseline_no_future_leakage(self):
        games=[{"season":2025,"week":i+1,"season_type":"REG","values":{"Passing yards":100+i*10,"Pass Attempts":20}} for i in range(9)]
        data={"source":"nflverse-stats-player-week","players":[{"position":"QB","games":games}]}
        first=audit(data)["markets"]["player_pass_yds"]["chronological_rolling_brier"]
        games[-1]["values"]["Passing yards"]=0
        second=audit(data)["markets"]["player_pass_yds"]["chronological_rolling_brier"]
        self.assertNotEqual(first,second)
    def test_reject_unknown_feed(self):
        with self.assertRaises(ValueError):
            audit({"source":"unknown","players":[]})
    def test_insufficient_data(self):
        result=audit({"source":"nflverse-stats-player-week","players":[]})
        self.assertEqual(result["total_samples"],0)
        self.assertEqual(result["markets"]["player_pass_yds"]["status"],"INSUFFICIENT_DATA")
if __name__=="__main__": unittest.main()
