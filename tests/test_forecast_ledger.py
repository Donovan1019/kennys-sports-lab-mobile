import unittest
from datetime import datetime,timezone,timedelta
from scripts.forecast_ledger import record,score
NOW=datetime(2026,10,21,12,tzinfo=timezone.utc)
def data(start=2):
 return ({"events":[{"event_id":"e","home":"H","away":"A","asof":NOW.isoformat(),"model_probability":.6}]},{"odds":[{"event_id":"e","commence_time":(NOW+timedelta(hours=start)).isoformat()}]})
class LedgerTests(unittest.TestCase):
 def test_append_and_idempotency(self):
  f,o=data();a=record({"forecasts":[]},f,o,NOW)
  self.assertEqual(a["added"],1)
  self.assertEqual(record(a,f,o,NOW)["added"],0)
 def test_no_post_start_forecast(self):
  f,o=data(-1)
  self.assertEqual(record({"forecasts":[]},f,o,NOW)["added"],0)
 def test_exact_id_only(self):
  f,o=data();ledger=record({"forecasts":[]},f,o,NOW)
  self.assertEqual(score(ledger,{"games":[{"event_id":"other","home":"H","away":"A","home_score":3,"away_score":2}]})["matched_forecasts"],0)
 def test_exact_outcome(self):
  f,o=data();ledger=record({"forecasts":[]},f,o,NOW)
  result=score(ledger,{"games":[{"event_id":"espn-123","date":(NOW+timedelta(hours=2)).isoformat(),"home":"H","away":"A","home_score":3,"away_score":2}]})
  self.assertEqual(result["matched_forecasts"],1)
  self.assertAlmostEqual(result["mean_brier"],.16)
  self.assertAlmostEqual(result["log_loss"],-__import__("math").log(.6),places=6)
  self.assertEqual(result["metrics_sample_size"],1)
  self.assertEqual(result["calibration_bins"][0]["count"],1)
 def test_ambiguous_matching_fails_closed(self):
  f,o=data();ledger=record({"forecasts":[]},f,o,NOW)
  game={"event_id":"provider","date":(NOW+timedelta(hours=2)).isoformat(),"home":"H","away":"A","home_score":3,"away_score":2}
  self.assertEqual(score(ledger,{"games":[game,dict(game,event_id="duplicate")]})["matched_forecasts"],0)
 def test_repeated_snapshots_count_once(self):
  f,o=data();first=record({"forecasts":[]},f,o,NOW)
  second=record(first,{"events":[dict(f["events"][0],asof=(NOW+timedelta(minutes=1)).isoformat())]},o,NOW+timedelta(minutes=1))
  game={"event_id":"provider","date":(NOW+timedelta(hours=2)).isoformat(),"home":"H","away":"A","home_score":3,"away_score":2}
  result=score(second,{"games":[game]})
  self.assertEqual(len(second["forecasts"]),2)
  self.assertEqual(result["matched_forecasts"],1)
  self.assertEqual(result["unique_events_in_ledger"],1)
 def test_different_start_rejected(self):
  f,o=data();ledger=record({"forecasts":[]},f,o,NOW)
  game={"event_id":"provider","date":(NOW+timedelta(hours=3)).isoformat(),"home":"H","away":"A","home_score":3,"away_score":2}
  self.assertEqual(score(ledger,{"games":[game]})["matched_forecasts"],0)
if __name__=="__main__":unittest.main()
