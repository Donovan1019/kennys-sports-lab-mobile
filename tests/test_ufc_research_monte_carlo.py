import unittest
from scripts.ufc_research_monte_carlo import run
class UFCResearchMonteCarloTests(unittest.TestCase):
    def test_reproducible_and_not_bet_eligible(self):
        f=[{"fight_id":"123","red":"A","blue":"B","sparse_data_probability":{"red":0.55,"red_uncertainty_interval":[0.3,0.8]}}]
        a=run(f,1000)
        self.assertEqual(a,run(f,1000))
        self.assertEqual(a[0]["status"],"HYPOTHETICAL_RESEARCH_ONLY")
        self.assertFalse(a[0]["bet_eligible"])
        self.assertIsNone(a[0]["model_ev"])
    def test_missing_inputs_block(self):
        self.assertEqual(run([{"fight_id":"1","red":"A","blue":"B"}])[0]["status"],"UNAVAILABLE")
if __name__=="__main__":unittest.main()
