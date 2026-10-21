import unittest
from datetime import datetime,timezone
from scripts.market_consensus import summarize
from scripts.three_sport_champion import capture

class ThreeSportQuoteProvenanceTests(unittest.TestCase):
    def test_timestamp_provenance_from_archived_quotes(self):
        now=datetime(2026,10,21,12,tzinfo=timezone.utc)
        archive={"quotes":[
            {"event_id":"e","away":"A","home":"H","bookmaker":"one","captured_at":"2026-10-21T11:55:00Z","home_no_vig":.6,"away_no_vig":.4},
            {"event_id":"e","away":"A","home":"H","bookmaker":"two","captured_at":"2026-10-21T11:56:00Z","home_no_vig":.58,"away_no_vig":.42}]}
        result=summarize(archive,now)
        q=result["events"][0]
        self.assertEqual(q["verified_quote_at"],"2026-10-21T11:56:00+00:00")
        self.assertEqual(q["earliest_quote_at"],"2026-10-21T11:55:00+00:00")
        ledger={"forecasts":[{"forecast_id":"id","event_id":"e","forecast_at":"2026-10-21T11:57:00Z","event_start":"2026-10-21T20:00:00Z"}]}
        self.assertEqual(len(capture({},ledger,result)["baselines"]),1)
        ledger["forecasts"][0]["forecast_at"]="2026-10-21T11:54:00Z"
        self.assertEqual(capture({},ledger,result)["baselines"],[])
    def test_old_consensus_without_timestamps_fails_closed(self):
        ledger={"forecasts":[{"forecast_id":"id","event_id":"e","forecast_at":"2026-10-21T11:57:00Z","event_start":"2026-10-21T20:00:00Z"}]}
        quotes={"events":[{"event_id":"e","bookmaker_count":2,"home_consensus_no_vig":.5}]}
        self.assertEqual(capture({},ledger,quotes)["baselines"],[])
if __name__=="__main__":
    unittest.main()
