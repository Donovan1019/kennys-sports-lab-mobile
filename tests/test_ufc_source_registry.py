import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class UFCSourceRegistryTests(unittest.TestCase):
    def test_registry_is_fail_closed(self):
        data = json.loads((ROOT / "config/ufc_source_registry.json").read_text())
        self.assertEqual(data["sport"], "UFC")
        self.assertIs(data["bet_eligible"], False)
        self.assertGreaterEqual(len(data["sources"]), 4)
        names = {item["name"]: item for item in data["sources"]}
        self.assertEqual(names["Tapology"]["automated_collection"], "PROHIBITED_WITHOUT_PERMISSION")
        self.assertEqual(names["UFC official website"]["automated_collection"], "PROHIBITED_WITHOUT_PERMISSION")
        self.assertIn("out_of_sample_calibration", data["required_before_model"])
        self.assertIn("independent_timestamped_odds", data["required_before_model"])
        for item in data["sources"]:
            self.assertTrue(item["role"])
            self.assertTrue(item["automated_collection"])
            self.assertTrue(item["notes"])

if __name__ == "__main__":
    unittest.main()
