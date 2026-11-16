"""Completed games must be appended as they finish, without rewriting prior finals."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import three_sport_results as results


class IncrementalResultsTests(unittest.TestCase):
    def test_collect_ignores_unfinished_games(self):
        def event(identifier, completed, score):
            return {"id": identifier, "name": "Away at Home", "date": "2026-11-15T18:00Z",
                    "status": {"type": {"completed": completed, "name": "STATUS_FINAL" if completed else "STATUS_IN_PROGRESS"}},
                    "competitions": [{"competitors": [
                        {"homeAway": "home", "score": str(score), "team": {"displayName": "Home"}},
                        {"homeAway": "away", "score": "10", "team": {"displayName": "Away"}}]}]}
        payload = {"events": [event("1", True, 24), event("2", False, 14)]}
        out = results.collect("NFL", "2026-11-15", fetcher=lambda _: payload)
        self.assertEqual([g["event_id"] for g in out["games"]], ["1"])

    def test_incremental_archive_keeps_prior_finals(self):
        # Exercise the same merge contract used by the scheduled collector.
        prior = [{"event_id": "1", "home_score": 24, "away_score": 10}]
        incoming = [{"event_id": "1", "home_score": 24, "away_score": 10},
                    {"event_id": "2", "home_score": 17, "away_score": 14}]
        merged = results.merge_completed_games(prior, incoming)
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0], prior[0])
        with self.assertRaises(ValueError):
            results.merge_completed_games(prior, [{"event_id": "1", "home_score": 25, "away_score": 10}])


if __name__ == "__main__":
    unittest.main()
