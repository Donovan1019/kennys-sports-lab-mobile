import unittest
from scripts.ufc_theoddsapi_adapter import convert

class ProviderAdapterTests(unittest.TestCase):
    def test_two_books(self):
        p={"success":True,"data":[{"event_id":"fight1","sport":"mma_mixed_martial_arts",
            "home_team":"A","away_team":"B","start_time":"2026-10-25T12:00:00Z",
            "books":[{"book":key,"market":"h2h","updated_at":"2026-10-23T12:00:00Z",
                      "outcomes":[{"name":"A","price":-120},{"name":"B","price":105}]}
                     for key in ("draftkings","fanduel")]}]}
        out=convert(p,"2026-10-23T13:00:00Z")
        self.assertEqual(len(out["draftkings"]["moneylines"]),2)
        self.assertEqual(len(out["fanduel"]["moneylines"]),2)
        self.assertFalse(out["draftkings"]["moneylines"][0]["model_calibrated"])
    def test_bad_response_fails(self):
        with self.assertRaises(ValueError): convert({"success":False},"2026-10-23T13:00:00Z")
    def test_finished_event_excluded(self):
        p={"success":True,"data":[{"event_id":"old","sport":"mma","home_team":"A",
            "away_team":"B","start_time":"2026-10-22T12:00:00Z","books":[]}]}
        self.assertEqual(convert(p,"2026-10-23T13:00:00Z")["draftkings"]["moneylines"],[])
if __name__=="__main__": unittest.main()
