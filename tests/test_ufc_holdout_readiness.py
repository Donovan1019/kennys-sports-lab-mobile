import unittest
from scripts.ufc_holdout_readiness import evaluate
def bout(i,w="A",l="B"):
    return {"event_id":"e"+str(i),"fight_id":str(i),"event_date":f"2026-01-{i:02d}T12:00:00Z",
            "winner":w,"loser":l,"winner_verified":True}
class UFCHoldoutReadinessTests(unittest.TestCase):
    def test_empty_and_one_event(self):
        self.assertEqual(evaluate([])["status"],"INSUFFICIENT_HISTORY")
        self.assertEqual(evaluate([bout(1)])["status"],"INSUFFICIENT_HISTORY")
    def test_holdout_has_temporal_cutoff_and_never_bet_eligible(self):
        result=evaluate([bout(i) for i in range(1,21)],min_prior=1)
        self.assertGreater(result["holdout_n"],0)
        self.assertFalse(result["bet_eligible"])
        self.assertEqual(result["status"],"INSUFFICIENT_HOLDOUT")
    def test_invalid_fraction(self):
        with self.assertRaises(ValueError):evaluate([],holdout_fraction=1)
if __name__=="__main__":unittest.main()
