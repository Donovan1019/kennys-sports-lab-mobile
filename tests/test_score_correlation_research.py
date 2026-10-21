import unittest
from datetime import datetime,timezone,timedelta
from scripts.score_correlation_research import estimate

NOW=datetime(2026,10,21,tzinfo=timezone.utc)
def game(i, date=None):
    return {"event_id":str(i),"date":(date or NOW-timedelta(days=i+1)).isoformat(),
            "away_score":10+i%9,"home_score":15+i%9}
class CorrelationResearchTests(unittest.TestCase):
    def test_future_and_same_kickoff_excluded(self):
        games=[game(i) for i in range(50)]
        games += [game(100,NOW),game(101,NOW+timedelta(days=1))]
        r=estimate(games,NOW)
        self.assertEqual(r["sample_size"],50)
        self.assertGreater(r["correlation"],0)
    def test_duplicate_id_excluded(self):
        games=[game(i) for i in range(50)]
        r=estimate(games+[dict(games[0])],NOW)
        self.assertEqual(r["sample_size"],50)
    def test_shrinkage(self):
        r=estimate([game(i) for i in range(50)],NOW)
        self.assertLess(r["correlation"],r["raw_correlation"])
    def test_insufficient_history(self):
        self.assertEqual(estimate([game(1)],NOW)["status"],"insufficient_history")
    def test_naive_cutoff_rejected(self):
        with self.assertRaises(ValueError):
            estimate([],datetime(2026,10,21))
if __name__=="__main__":
    unittest.main()
