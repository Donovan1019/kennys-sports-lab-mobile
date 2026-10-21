import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from scripts.three_sport_player_input_integrity import assess

class InputIntegrityTests(unittest.TestCase):
    def test_flattened_quote_feed_and_invalid_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "feed").mkdir()
            for slug, history in (
                ("americanfootball_nfl", "nfl_player_stats.json"),
                ("basketball_nba", "nba_player_stats.json"),
                ("icehockey_nhl", "nhl_official_player_stats.json"),
            ):
                (root / "feed" / history).write_text(json.dumps({"players": [{"name": "Example"}]}))
                (root / "feed" / (slug + ".json")).write_text(json.dumps({"odds": [
                    {"event_id": "e1", "bookmaker": "draftkings", "market": "h2h",
                     "selection": "Home", "price": -120, "updated_at": "2026-10-21T14:00:00Z",
                     "commence_time": "2026-10-22T00:00:00Z"},
                    {"event_id": "e2", "bookmaker": "draftkings", "market": "h2h",
                     "selection": "Away", "price": 0, "updated_at": "2026-10-21T14:00:00Z",
                     "commence_time": "2026-10-22T00:00:00Z"},
                ]}))
            report = assess(datetime(2026, 10, 21, 14, 30, tzinfo=timezone.utc), root)
            for sport in ("NFL", "NBA", "NHL"):
                row = report["sports"][sport]
                self.assertEqual(row["archived_market_types"], ["h2h"])
                self.assertEqual(row["valid_archived_quote_rows"], 1)
                self.assertEqual(row["invalid_archived_quote_rows"], 1)
                self.assertEqual(row["future_event_count_with_archived_quotes"], 1)
                self.assertTrue(row["fresh_quote_timestamp_within_60m"])
                self.assertFalse(row["live_event_matched_player_props_verified"])
                self.assertEqual(row["verified_betting_recommendations"], 0)

if __name__ == "__main__":
    unittest.main()
