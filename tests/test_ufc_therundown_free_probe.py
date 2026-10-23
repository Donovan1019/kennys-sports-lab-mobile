import unittest
from scripts.ufc_therundown_free_probe import catalog_report,request_catalog

class ProbeTests(unittest.TestCase):
    def test_catalog_discovery(self):
        r=catalog_report({"data":[{"id":9,"name":"UFC / MMA"}]},
                         {"data":[{"id":19,"name":"DraftKings"},{"id":23,"name":"FanDuel"}]},
                         {"data":[{"id":1,"name":"Moneyline"}]})
        self.assertEqual(len(r["sport_candidates"]),1)
        self.assertEqual(len(r["book_candidates"]),2)
        self.assertFalse(r["live_connected"])
        self.assertFalse(r["bet_eligible"])
    def test_no_unauthorized_path(self):
        with self.assertRaises(ValueError):request_catalog("events","test")
    def test_no_key(self):
        with self.assertRaises(ValueError):request_catalog("sports","")
if __name__=="__main__":unittest.main()
