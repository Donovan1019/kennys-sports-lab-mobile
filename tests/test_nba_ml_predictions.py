import datetime as dt
import unittest
from scripts.build_nba_ml_predictions import build
NOW=dt.datetime(2026,10,28,16,tzinfo=dt.timezone.utc)
class ModelFeedTests(unittest.TestCase):
 def test_independent_ratings_required(self):
  with self.assertRaises(ValueError):
   build({"status":"ok","sport":"basketball_nba","odds":[]},{"status":"unavailable"},NOW)
 def test_complementary_probabilities(self):
  teams={f"Team {i}":float(i) for i in range(28)}
  teams.update({"Atlanta Hawks":2.0,"Miami Heat":1.0})
  ratings={"status":"validated","calibration_passed":True,"training_cutoff":"2026-10-27T00:00:00Z","validation_report":"test-fixture","season":"2026-27","teams":teams,"logistic_scale":4}
  odds={"status":"ok","sport":"basketball_nba","odds":[{"market":"h2h","event_id":"game","event":"Miami Heat @ Atlanta Hawks","commence_time":"2026-10-28T23:10:00Z"}]}
  out=build(odds,ratings,NOW)
  self.assertEqual(len(out["predictions"]),2)
  self.assertAlmostEqual(sum(p["win_probability"] for p in out["predictions"]),1,places=5)
if __name__=="__main__":unittest.main()
