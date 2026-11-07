import unittest
from scripts.ufc_simulator_input_audit import audit

class UFCInputAuditTests(unittest.TestCase):
    def test_distinguishes_profile_from_simulator_readiness(self):
        card={"fights":[{"id":"1","red":"José Souza","blue":"Test Fighter","scheduled_rounds":None}]}
        mirror={"fighters":[{"name":"José Souza","status":"INSUFFICIENT_OR_AMBIGUOUS"},{"name":"Test Fighter","status":"MATCHED_HISTORICAL_STATS","career_round_totals":{"round_rows":5}}]}
        sims={"blocked":[{"fight_id":"1","reason":"Missing fighter stats: red"}]}
        result=audit(card,mirror,sims)
        self.assertEqual(result["ambiguous_historical_sides"],1)
        self.assertEqual(result["matched_historical_sides"],1)
        self.assertEqual(result["absent_historical_sides"],0)
        self.assertEqual(result["verified_scheduled_round_fights"],0)
        self.assertEqual(result["blocked_fights"],1)
        self.assertFalse(result["bet_eligible"])
    def test_missing_profile_not_confused_with_ambiguous(self):
        result=audit({"fights":[{"id":2,"red":"Unknown","blue":"Other","scheduled_rounds":3}]},{"fighters":[]},{"blocked":[]})
        self.assertEqual(result["absent_historical_sides"],2)
        self.assertEqual(result["verified_scheduled_round_fights"],1)
        self.assertFalse(result["bet_eligible"])
if __name__ == "__main__": unittest.main()
