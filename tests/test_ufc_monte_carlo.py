import copy
import json
import tempfile
import unittest
from pathlib import Path
from scripts.ufc_monte_carlo import simulate,export

FIGHT={"id":"verified-fixture-1","red":"A","blue":"B","start_time":"2026-11-01T01:00:00Z",
       "scheduled_rounds":3,"stats_verified":True,"fighter_status_verified":True,
       "red_stats":{"ko_rate":0.5,"submission_rate":0.2,"decision_rate":0.3,"sample_size":15},
       "blue_stats":{"ko_rate":0.2,"submission_rate":0.3,"decision_rate":0.5,"sample_size":18}}
class UFCMonteCarloTests(unittest.TestCase):
    def test_deterministic_and_conservative(self):
        a=simulate(FIGHT,1000)
        self.assertEqual(a,simulate(FIGHT,1000))
        self.assertFalse(a["bet_eligible"])
        self.assertEqual(a["model_status"],"UNCALIBRATED_RESEARCH_ONLY")
        self.assertAlmostEqual(sum(a["winner_probability"].values()),1)
        self.assertAlmostEqual(sum(a["method_probability"].values()),1)
        self.assertAlmostEqual(sum(a["ending_round_probability"].values()),1)
    def test_rejects_missing_verification(self):
        bad=copy.deepcopy(FIGHT)
        bad["stats_verified"]=False
        with self.assertRaises(ValueError):simulate(bad,1000)
    def test_rejects_invalid_rates(self):
        bad=copy.deepcopy(FIGHT)
        bad["red_stats"]["ko_rate"]=0.9
        with self.assertRaises(ValueError):simulate(bad,1000)
    def test_missing_stats_are_blocked_not_simulated(self):
        with tempfile.TemporaryDirectory() as d:
            inp=Path(d)/"in.json";out=Path(d)/"out.json"
            inp.write_text(json.dumps({"fights":[{"id":"1","red":"A","blue":"B","start_time":"2026-11-01T01:00:00Z"}]}))
            payload=export(inp,out)
            self.assertEqual(payload["simulations"],[])
            self.assertEqual(len(payload["blocked"]),1)
            self.assertFalse(payload["bet_eligible"])
if __name__=="__main__":unittest.main()
