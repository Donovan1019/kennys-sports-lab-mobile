import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from scripts.verify_nfl_archive_write import verify

class ArchiveWriteVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "feed").mkdir()
        self.stamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
        self.iso = self.stamp.isoformat()
        self.folder = self.root / "archive/nfl_moneyline/inputs"
        self.folder.mkdir(parents=True)
        (self.root / "feed/independent_game_inputs.json").write_text(json.dumps({"source_games_fetched_at": self.iso}))
        self.file = self.folder / (self.stamp.strftime("%Y%m%dT%H%M%SZ") + ".json")
    def tearDown(self):
        self.temp.cleanup()
    def test_valid_archive(self):
        self.file.write_text(json.dumps({"source_timestamp": self.iso, "games": [{"event_id": "1"}]}))
        verify("inputs", self.root)
    def test_missing_archive_fails(self):
        with self.assertRaises(FileNotFoundError):
            verify("inputs", self.root)
    def test_empty_archive_fails(self):
        self.file.write_text(json.dumps({"source_timestamp": self.iso, "games": []}))
        with self.assertRaises(ValueError):
            verify("inputs", self.root)
    def test_timestamp_mismatch_fails(self):
        self.file.write_text(json.dumps({"source_timestamp": "2026-01-01T00:00:00Z", "games": [{"event_id": "1"}]}))
        with self.assertRaises(ValueError):
            verify("inputs", self.root)

if __name__ == "__main__":
    unittest.main()
