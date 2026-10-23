import unittest
from scripts.ufc_tidytuesday_elo import build

def fight(date,url,w,l):
    return {"event_date":date,"source_fight_url":url,"winner":w,"loser":l,"independently_verified":False}

class UFCImportedEloTests(unittest.TestCase):
    def test_same_day_outcomes_do_not_leak(self):
        base=[fight("2026-01-01","a","A","B"),fight("2026-01-01","b","A","B")]
        report=build({"snapshot":"2026-07-07","bet_eligible":False,"fight_history":{"rows":base}},min_bouts=1)
        self.assertEqual(report["pre_event_evaluated_fights"],0)
        report=build({"snapshot":"2026-07-07","bet_eligible":False,
                      "fight_history":{"rows":base+[fight("2026-01-02","c","B","A")]}},min_bouts=1)
        self.assertEqual(report["pre_event_evaluated_fights"],1)
        self.assertFalse(report["bet_eligible"])
        self.assertFalse(report["independently_verified"])
    def test_reject_betting_flag(self):
        with self.assertRaises(ValueError):
            build({"snapshot":"2026-07-07","bet_eligible":True,"fight_history":{"rows":[]}})
if __name__=="__main__":
    unittest.main()
