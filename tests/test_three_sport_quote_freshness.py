"""Regression coverage: freshly republished stale sportsbook quotes remain rejected."""
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import three_sport_backtest as audit


class QuoteFreshnessTests(unittest.TestCase):
    def test_fresh_wrapper_does_not_resurrect_stale_quote(self):
        now = dt.datetime(2026, 11, 16, 12, tzinfo=dt.timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "feed").mkdir()
            feed = {
                "fetched_at": (now - dt.timedelta(minutes=2)).isoformat(),
                "odds": [{
                    "event": "Away @ Home", "market": "player_points",
                    "player": "Example Player", "bookmaker": "example",
                    "price": -110,
                    "commence_time": (now + dt.timedelta(hours=6)).isoformat(),
                    "updated_at": (now - dt.timedelta(days=2)).isoformat()
                }]
            }
            (root / "feed" / "nfl_props.json").write_text(json.dumps(feed))
            with patch.object(audit, "ROOT", root), patch.object(audit, "SPORTS", {"NFL": "nfl_props.json"}):
                report = audit.capture(now)
            self.assertEqual(report["NFL"]["eligible_quotes"], 0)
            self.assertEqual(report["NFL"]["rejected_quotes"], 1)
            snapshots = list((root / "backtests" / "snapshots").rglob("nfl.json"))
            self.assertEqual(len(snapshots), 1)
            saved = json.loads(snapshots[0].read_text())
            self.assertIn("stale_quote_over_24h", saved["rejected_quotes"][0]["audit_flags"])


if __name__ == "__main__":
    unittest.main()
