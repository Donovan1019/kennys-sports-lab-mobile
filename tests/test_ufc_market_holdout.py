import unittest
from scripts.ufc_market_holdout import american_probability, score

class MarketHoldoutTests(unittest.TestCase):
    def test_american_prices(self):
        self.assertAlmostEqual(american_probability(-150),0.6)
        self.assertAlmostEqual(american_probability(200),1/3)
        with self.assertRaises(ValueError):
            american_probability(50)
    def test_match_and_no_vig(self):
        predictions=[{"event_id":"E","fight_id":"1","winner":"A","loser":"B","winner_probability":0.6}]
        odds=[{"event_id":"E","fight_id":"1","winner":"A","loser":"B",
               "winner_american_odds":-120,"loser_american_odds":110,
               "source_verified":True,"pre_fight_verified":True}]
        r=score(predictions,odds)
        self.assertEqual(r["holdout_matched_fights"],1)
        self.assertFalse(r["independently_verified"])
        self.assertIsNotNone(r["market_brier"])
    def test_unverified_and_duplicates_excluded(self):
        predictions=[{"event_id":"E","fight_id":"1","winner":"A","loser":"B","winner_probability":0.6}]
        odds=[{"event_id":"E","fight_id":"1","winner":"A","loser":"B",
               "winner_american_odds":-120,"loser_american_odds":110,
               "source_verified":True,"pre_fight_verified":True}]
        self.assertEqual(score(predictions,odds*2)["holdout_matched_fights"],0)
        odds[0]["pre_fight_verified"]=False
        self.assertEqual(score(predictions,odds)["holdout_matched_fights"],0)
if __name__=="__main__":
    unittest.main()
