import unittest
from scripts.ufc_point_in_time_gate import validate,audit

class PointInTimeTests(unittest.TestCase):
    def row(self):
        return {"fight_id":"f1","fighter_id":"p1","feature_name":"sig_strikes_per_round","value":4.1,
                "source_event_time":"2026-01-01T00:00:00Z",
                "source_published_at":"2026-01-02T00:00:00Z",
                "captured_at":"2026-01-03T00:00:00Z",
                "prediction_cutoff":"2026-01-04T00:00:00Z",
                "source_sha256":"a"*64}
    def test_accepts_prior_snapshot(self):
        self.assertTrue(validate(self.row()))
    def test_rejects_post_cutoff_capture(self):
        row=self.row()
        row["captured_at"]="2026-01-05T00:00:00Z"
        with self.assertRaises(ValueError):validate(row)
    def test_rejects_post_cutoff_publication(self):
        row=self.row()
        row["source_published_at"]="2026-01-05T00:00:00Z"
        with self.assertRaises(ValueError):validate(row)
    def test_rejects_future_event(self):
        row=self.row()
        row["source_event_time"]="2026-01-05T00:00:00Z"
        with self.assertRaises(ValueError):validate(row)
    def test_rejects_naive_timestamp(self):
        row=self.row()
        row["captured_at"]="2026-01-03T00:00:00"
        with self.assertRaises(ValueError):validate(row)
    def test_rejects_missing_lineage(self):
        row=self.row()
        del row["source_sha256"]
        with self.assertRaises(ValueError):validate(row)
    def test_rejects_duplicate_features(self):
        row=self.row()
        result=audit([row,dict(row)])
        self.assertEqual(result["accepted"],1)
        self.assertEqual(result["rejected"],1)

if __name__=="__main__":unittest.main()
