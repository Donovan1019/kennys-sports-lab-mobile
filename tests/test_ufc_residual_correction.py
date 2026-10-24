import unittest
from scripts.ufc_residual_correction import assess

class ResidualCorrectionTests(unittest.TestCase):
    def rows(self, model_good):
        rows=[]
        for i in range(120):
            y=i%2
            rows.append({"date":f"{2020+i//12}-{i%12+1:02d}-01",
                         "market":.65 if y else .35,
                         "p":(.85 if y else .15) if model_good else (.15 if y else .85),
                         "y":y})
        return rows

    def test_rejects_bad_fighter_model(self):
        result=assess(self.rows(False))
        self.assertEqual(result["selected_residual_weight"],0)
        self.assertFalse(result["bet_eligible"])

    def test_keeps_beneficial_correction(self):
        result=assess(self.rows(True))
        self.assertGreater(result["selected_residual_weight"],0)
        self.assertTrue(result["improves_held_out_market"])

    def test_insufficient_history(self):
        with self.assertRaises(ValueError):
            assess(self.rows(True)[:5])

if __name__=="__main__":
    unittest.main()
