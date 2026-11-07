import unittest
from datetime import datetime,timezone
from scripts.ufc_refresh_odds import convert
class OddsRefreshTests(unittest.TestCase):
    def test_converts_two_sided_bookmaker_market(self):
        now=datetime(2026,11,7,tzinfo=timezone.utc)
        event={"id":"fight-1","commence_time":"2026-11-08T00:00:00Z","away_team":"A","home_team":"B","bookmakers":[{"key":"draftkings","last_update":"2026-11-07T23:00:00Z","markets":[{"key":"h2h","outcomes":[{"name":"A","price":120},{"name":"B","price":-140}]}]}]}
        result=convert([event],now)
        self.assertEqual(len(result["odds"]),2)
        self.assertEqual(result["odds"][0]["bookmaker"],"draftkings")
        self.assertEqual(result["source"],"the-odds-api-v4")
    def test_ignores_other_books_and_markets(self):
        event={"id":"fight-1","commence_time":"2026-11-08T00:00:00Z","bookmakers":[{"key":"other","markets":[{"key":"h2h","outcomes":[{"name":"A","price":100}]}]},{"key":"fanduel","markets":[{"key":"totals","outcomes":[{"name":"Over","price":-110}]}]}]}
        self.assertEqual(convert([event],datetime.now(timezone.utc))["odds"],[])
if __name__=="__main__":unittest.main()
