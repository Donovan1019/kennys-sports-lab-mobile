import unittest
from scripts.ufc_import_historical_csv import convert

class HistoricalImportTests(unittest.TestCase):
    def test_verified_result_and_event_join(self):
        e=[{"EVENT":"UFC Test","DATE":"October 10, 2025"}]
        f=[{"EVENT":"UFC Test","BOUT":"A vs. B","OUTCOME":"W/L"},
           {"EVENT":"UFC Test","BOUT":"C vs. D","OUTCOME":"L/W"},
           {"EVENT":"UFC Test","BOUT":"E vs. F","OUTCOME":"D/D"}]
        r=convert(e,f)
        self.assertEqual(len(r["results"]),2)
        self.assertEqual(r["results"][0]["event_date"],"2025-10-10T12:00:00+00:00")
        self.assertEqual({x["winner"] for x in r["results"]},{"A","D"})
        self.assertEqual(r["conversion_audit"]["excluded_unverified_result"],1)
        self.assertFalse(r["bet_eligible"])
    def test_conflicting_event_dates_rejected(self):
        e=[{"EVENT":"UFC Test","DATE":"October 10, 2025"},
           {"EVENT":"UFC Test","DATE":"October 11, 2025"}]
        r=convert(e,[{"EVENT":"UFC Test","BOUT":"A vs. B","OUTCOME":"W/L"}])
        self.assertEqual(len(r["results"]),0)
    def test_duplicate_rejected(self):
        e=[{"EVENT":"UFC Test","DATE":"October 10, 2025"}]
        f={"EVENT":"UFC Test","BOUT":"A vs. B","OUTCOME":"W/L"}
        r=convert(e,[f,f])
        self.assertEqual(r["conversion_audit"]["excluded_duplicate"],1)
if __name__=="__main__":
    unittest.main()
