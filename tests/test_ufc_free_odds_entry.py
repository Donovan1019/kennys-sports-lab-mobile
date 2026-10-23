import unittest
from scripts.ufc_free_odds_entry import build

class FreeEntryTests(unittest.TestCase):
    def entry(self):
        return {"book":"draftkings","event_id":"example","fighter":"A","opponent":"B",
                "fighter_odds":-120,"opponent_odds":105,"event_start_utc":"2026-10-24T18:00:00Z"}
    def test_free_manual_entry(self):
        r=build([self.entry()],"2026-10-23T12:00:00Z")
        self.assertEqual(len(r["draftkings"]["moneylines"]),1)
        self.assertEqual(len(r["fanduel"]["moneylines"]),0)
        self.assertFalse(r["draftkings"]["moneylines"][0]["source_verified"])
    def test_unknown_book_rejected(self):
        x=self.entry()
        x["book"]="other"
        with self.assertRaises(ValueError):build([x],"2026-10-23T12:00:00Z")
    def test_post_event_rejected(self):
        with self.assertRaises(ValueError):build([self.entry()],"2026-10-25T12:00:00Z")
if __name__=="__main__":unittest.main()
