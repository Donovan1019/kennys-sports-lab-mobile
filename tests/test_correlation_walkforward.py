import unittest
from datetime import datetime,timezone,timedelta
from scripts.correlation_walkforward import compare

BASE=datetime(2026,1,1,tzinfo=timezone.utc)
def games():
    rows=[]
    for i in range(80):
        date=BASE+timedelta(days=i)
        rows.append({"event_id":str(i),"date":date.isoformat(),
                     "away":"A","home":"B",
                     "away_score":15+i%8,"home_score":19+(i*3)%10})
    return rows

class WalkforwardTests(unittest.TestCase):
    def test_comparison_no_automatic_promotion(self):
        result=compare(games(),trials=1000,min_history=40,max_games=2)
        self.assertEqual(result["sample_size"],2)
        self.assertFalse(result["promotion_approved"])
        self.assertEqual(result["independent"]["sample_size"],2)
        self.assertEqual(result["correlated"]["sample_size"],2)
        self.assertGreaterEqual(result["results"][0]["history_size"],40)
    def test_no_future_information(self):
        earlier=games()
        first=compare(earlier,trials=1000,min_history=40,max_games=1)
        future=dict(earlier[-1],event_id="future",date=(BASE+timedelta(days=500)).isoformat(),away_score=999,home_score=1)
        second=compare(earlier+[future],trials=1000,min_history=40,max_games=1)
        self.assertEqual(first["results"],second["results"])
    def test_empty(self):
        self.assertEqual(compare([],trials=1000)["sample_size"],0)
    def test_bad_trials(self):
        with self.assertRaises(ValueError):
            compare([],trials=99)

if __name__=="__main__":
    unittest.main()
