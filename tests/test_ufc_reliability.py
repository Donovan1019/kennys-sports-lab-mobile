import unittest
from scripts.ufc_reliability import reliability
def row(i,p=.7,y=True):
    return {"fight_id":str(i),"red_win_probability":p,"red_won":y,"prefight_verified":True}
class UFCReliabilityTests(unittest.TestCase):
    def test_brier_ece_and_sample_gate(self):
        result=reliability([row(1),row(2,.3,False)],bins=2)
        self.assertEqual(result["graded"],2)
        self.assertAlmostEqual(result["brier"],.09)
        self.assertAlmostEqual(result["expected_calibration_error"],.3)
        self.assertFalse(result["bet_eligible"])
    def test_duplicate_and_unverified_rejected(self):
        bad=row(3);bad["prefight_verified"]=False
        r=reliability([row(1),row(1),bad])
        self.assertEqual(r["graded"],1)
        self.assertEqual(r["rejected"],2)
    def test_empty_is_not_approved(self):
        r=reliability([])
        self.assertIsNone(r["brier"])
        self.assertEqual(r["status"],"INSUFFICIENT_SAMPLE")
    def test_bad_probabilities_rejected(self):
        self.assertEqual(reliability([row(1,p=1.5)])["graded"],0)
if __name__=="__main__":unittest.main()
