import unittest
from scripts.ufc_tidytuesday_holdout import audit

def report():
    rows=[]
    for day in range(1,11):
        for i in range(20):
            rows.append({"date":f"2026-01-{day:02d}","fight_url":f"fight-{day}-{i}",
                         "winner_probability":0.6,"bet_eligible":False})
    return {"bet_eligible":False,"independently_verified":False,"forecasts":rows}

class HoldoutTests(unittest.TestCase):
    def test_split_on_dates_without_overlap(self):
        result=audit(report(),fraction=0.2,minimum_holdout=30)
        self.assertEqual(result["holdout_start"],"2026-01-09")
        self.assertEqual(result["train"]["n"],160)
        self.assertEqual(result["holdout"]["n"],40)
        self.assertTrue(result["enough_holdout"])
        self.assertFalse(result["bet_eligible"])
    def test_reject_betting_flag(self):
        r=report()
        r["bet_eligible"]=True
        with self.assertRaises(ValueError): audit(r)
if __name__=="__main__":
    unittest.main()
