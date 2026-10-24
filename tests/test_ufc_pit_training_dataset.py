import unittest
from scripts.ufc_pit_training_dataset import assemble

class Tests(unittest.TestCase):
 def setUp(self):
  self.label={"fight_id":"fight1","prediction_time":"2026-01-04T00:00:00Z","fight_time":"2026-01-05T00:00:00Z","red_won":"1"}
  self.feature={"fight_id":"fight1","fighter_id":"fighter1","feature_name":"strikes_per_round","value":4.2,
    "source_event_time":"2026-01-01T00:00:00Z","source_published_at":"2026-01-02T00:00:00Z",
    "captured_at":"2026-01-03T00:00:00Z","prediction_cutoff":"2026-01-04T00:00:00Z",
    "source_sha256":"a"*64}
 def test_assemble(self):
  data=assemble([self.label],[self.feature])
  self.assertEqual(data[0]["features"]["fighter1:strikes_per_round"],4.2)
 def test_reject_future_capture(self):
  self.feature["captured_at"]="2026-01-05T00:00:00Z"
  with self.assertRaises(ValueError):assemble([self.label],[self.feature])
 def test_reject_wrong_cutoff(self):
  self.feature["prediction_cutoff"]="2026-01-03T00:00:00Z"
  with self.assertRaises(ValueError):assemble([self.label],[self.feature])
 def test_reject_missing_features(self):
  with self.assertRaises(ValueError):assemble([self.label],[])
 def test_reject_duplicate(self):
  with self.assertRaises(ValueError):assemble([self.label],[self.feature,self.feature])
if __name__=="__main__":unittest.main()
