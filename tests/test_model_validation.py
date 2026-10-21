import unittest
from scripts.model_validation import summarize

def row(date,p_ind,p_corr,y):
    return {"date":date,"independent":{"home_win_probability":p_ind,"home_won":y},
            "correlated":{"home_win_probability":p_corr,"home_won":y}}

class ModelValidationTests(unittest.TestCase):
    def test_empty(self):
        r=summarize({"results":[]},"americanfootball_nfl",replicates=100)
        self.assertEqual(r["sample_size"],0)
        self.assertFalse(r["promotion_approved"])
    def test_consistently_better_correlated(self):
        rows=[row(f"2025-09-{(i%20)+1:02d}T18:00:00+00:00",.4,.8,1) for i in range(40)]
        r=summarize({"results":rows},"americanfootball_nfl",replicates=200)
        self.assertLess(r["paired_block_bootstrap_95_interval"][1],0)
        self.assertFalse(r["promotion_approved"])
    def test_season_split_and_determinism(self):
        rows=[row("2025-05-01T00:00:00+00:00",.5,.6,1),
              row("2025-11-01T00:00:00+00:00",.5,.6,1)]
        a=summarize({"results":rows},"basketball_nba",replicates=100)
        b=summarize({"results":rows},"basketball_nba",replicates=100)
        self.assertEqual(a,b)
        self.assertEqual(len(a["seasons"]),2)
    def test_invalid_probability_ignored(self):
        r=summarize({"results":[row("2025-10-01T00:00:00+00:00",float("nan"),.5,1)]},
                    "americanfootball_nfl",replicates=100)
        self.assertEqual(r["sample_size"],0)
if __name__=="__main__":
    unittest.main()
