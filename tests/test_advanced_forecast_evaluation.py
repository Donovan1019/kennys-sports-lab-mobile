import unittest
from scripts.advanced_forecast_evaluation import evaluate, wilson_interval

class AdvancedEvaluationTests(unittest.TestCase):
    def test_empty_does_not_claim_edge(self):
        r = evaluate({"scored": [], "unmatched_events": 28})
        self.assertEqual(r["sample_size"], 0)
        self.assertEqual(r["future_or_unmatched_events"], 28)
        self.assertFalse(r["edge_claim_allowed"])

    def test_perfect_predictions_are_not_overstated(self):
        r = evaluate({"scored": [
            {"home_probability": 0.8, "home_won": 1},
            {"home_probability": 0.2, "home_won": 0}]})
        self.assertEqual(r["sample_size"], 2)
        self.assertAlmostEqual(r["brier"], 0.04)
        self.assertEqual(r["classification_accuracy"], 1)
        self.assertLess(r["classification_accuracy_wilson_95"][0], 1)
        self.assertFalse(r["edge_claim_allowed"])

    def test_invalid_rows_excluded(self):
        r = evaluate({"scored": [
            {"home_probability": float("nan"), "home_won": 1},
            {"home_probability": 0.7, "home_won": 1},
            {"home_probability": 1.2, "home_won": 0},
            {"home_probability": 0.6, "home_won": True}]})
        self.assertEqual(r["sample_size"], 1)

    def test_wilson_empty(self):
        self.assertIsNone(wilson_interval(0, 0))

if __name__ == "__main__":
    unittest.main()
