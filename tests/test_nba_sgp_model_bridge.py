"""Regression checks for the existing NBA SGP bridge. No betting picks generated."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import nba_sgp_model_ledger_bridge as bridge

class BridgeIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.source=self.base/"model.json"
        self.report=self.base/"status.json"
        self.ledger=self.base/"ledger.jsonl"
        self.patches=[
            patch.object(bridge,"SOURCE",self.source),
            patch.object(bridge,"REPORT",self.report),
            patch.object(bridge,"LEDGER",self.ledger),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def test_missing_source_never_creates_illustrated_picks(self):
        result=bridge.run()
        self.assertEqual(result["captured"],0)
        self.assertFalse(result["source_present"])
        self.assertFalse(result["capture_ready"])
        self.assertEqual(result["rejected_count"],0)
        self.assertFalse(self.ledger.exists())
        self.assertFalse(result["capture_ready"])
        self.assertEqual(json.loads(self.report.read_text())["status"],"NO_NEW_VERIFIED_MODEL_RECOMMENDATIONS")

    def test_research_only_without_simulation_cannot_be_promoted(self):
        self.source.write_text(json.dumps({"recommendations":[{
            "sgp_id":"test-only-no-picks",
            "model_recommendation":True,
            "research_only":True,
            "bet_eligible":False,
            "model_probability":0.7,
            "model_version":"test-only",
            "model_source":"test-only",
            "legs":[]
        }]}))
        result=bridge.run()
        self.assertEqual(result["captured"],0)
        self.assertEqual(len(result["rejected"]),1)
        self.assertEqual(result["status"],"PARTIAL_REJECTED")
        self.assertFalse(result["capture_ready"])
        self.assertFalse(self.ledger.exists())

    def test_unvalidated_walkforward_cannot_be_archived(self):
        self.source.write_text(json.dumps({"recommendations":[{
            "sgp_id":"test-only-unvalidated",
            "model_recommendation":True,"research_only":True,"bet_eligible":False,
            "model_probability":0.55,"joint_simulation_id":"test-only",
            "correlation_model_version":"test-only","simulation_validated":True,
            "backtest":{"method":"walk_forward","passed":False,"sample_size":100,"brier":0.2},
            "simulations":10000
        }]}))
        result=bridge.run()
        self.assertEqual(result["captured"],0)
        self.assertTrue(any(term in result["rejected"][0] for term in ("walk-forward", "promotion not approved")))
        self.assertFalse(self.ledger.exists())

    def test_nonfinite_joint_probability_rejected(self):
        self.source.write_text(json.dumps({"recommendations":[{
            "sgp_id":"test-only-nonfinite",
            "model_recommendation":True,
            "research_only":True,
            "bet_eligible":False,
            "model_probability":float("nan")
        }]}))
        result=bridge.run()
        self.assertEqual(result["captured"],0)
        self.assertTrue(any(term in result["rejected"][0] for term in ("non-finite", "missing calibrated joint model probability", "promotion not approved")))
        self.assertFalse(self.ledger.exists())

if __name__=="__main__":
    unittest.main()
