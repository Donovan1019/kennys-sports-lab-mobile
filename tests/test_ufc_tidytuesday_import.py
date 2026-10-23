import unittest
from scripts.ufc_tidytuesday_import import historical_fights, modeling_rows

class TestUFCImport(unittest.TestCase):
    def test_historical_winner_and_dedupe(self):
        r={"fight_url":"http://www.ufcstats.com/fight-details/abc","date":"2026-03-28",
           "f1_name":"A","f2_name":"B","f1_result":"W","f2_result":"L","method":"KO/TKO"}
        good,bad=historical_fights([r,r,{**r,"fight_url":"invalid"}])
        self.assertEqual(len(good),1)
        self.assertEqual(len(bad),2)
        self.assertFalse(good[0]["independently_verified"])
    def test_postfight_features_excluded(self):
        r={"date":"2026-03-28","r_fighter":"A","b_fighter":"B","winner":"Red",
           "finish":"KO/TKO","finish_round":"2","r_wins":"8","r_odds":"-150"}
        good,bad=modeling_rows([r])
        self.assertFalse(bad)
        self.assertEqual(good[0]["features"]["r_wins"],8.0)
        self.assertNotIn("finish",good[0]["features"])
        self.assertNotIn("winner",good[0]["features"])
        self.assertFalse(good[0]["odds_timestamp_verified"])
        self.assertFalse(good[0]["bet_eligible"])
    def test_reject_future_and_draw(self):
        r={"date":"2099-01-01","r_fighter":"A","b_fighter":"B","winner":"Draw"}
        good,bad=modeling_rows([r])
        self.assertFalse(good)
        self.assertEqual(len(bad),1)
if __name__=="__main__":
    unittest.main()
