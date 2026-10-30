import unittest
from scripts.ufc_historical_odds_candidates import convert

class OddsCandidateTests(unittest.TestCase):
    def test_valid_pair_remains_unverified(self):
        row={"event_name":"Test","event_date":"2024-01-01","fighter1":"A","fighter2":"B",
             "favourite":"B","underdog":"A","favourite_odds":"1.5","underdog_odds":"2.7",
             "outcome":"fighter1","odds_extract_ts":"2025-01-01"}
        r=convert([row,row])
        self.assertEqual(r["audit"]["matched_candidates"],1)
        self.assertEqual(r["audit"]["excluded_duplicate"],1)
        x=r["odds_candidates"][0]
        self.assertEqual(x["winner_decimal_odds"],2.7)
        self.assertFalse(x["pre_fight_verified"])
        self.assertFalse(r["bet_eligible"])
    def test_draw_rejected(self):
        row={"event_name":"Test","event_date":"2024-01-01","fighter1":"A","fighter2":"B",
             "outcome":"Draw"}
        self.assertEqual(convert([row])["audit"]["matched_candidates"],0)
if __name__=="__main__":
    unittest.main()
