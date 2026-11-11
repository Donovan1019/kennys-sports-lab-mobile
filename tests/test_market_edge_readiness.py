import json
import tempfile
import unittest
from pathlib import Path
from scripts.market_edge_readiness import inspect

class MarketEdgeReadinessTests(unittest.TestCase):
    def test_missing_sources_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            status = inspect(Path(temp))
            self.assertEqual(status["status"], "UNAVAILABLE")
            self.assertEqual(set(status["sports"]), {"NBA","NHL","NFL","NCAAB"})
            self.assertTrue(all(not x["betting_ready"] for x in status["sports"].values()))
    def test_research_only_not_promoted(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            p=root/"feed/basketball_nba_pregame_research.json"
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps({"status":"experimental_research_only","events":[{"event":"A vs B"}]}))
            report=inspect(root)
            self.assertEqual(report["sports"]["NBA"]["model"]["events"],1)
            self.assertFalse(report["sports"]["NBA"]["betting_ready"])
