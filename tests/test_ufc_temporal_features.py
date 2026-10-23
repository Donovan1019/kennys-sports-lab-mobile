import unittest
from scripts.ufc_temporal_features import features
def fight(fid,date,w="A",l="B"):
    return {"event_id":"e"+str(fid),"fight_id":str(fid),"event_date":date,
            "winner":w,"loser":l,"winner_verified":True}
class UFCTemporalFeatureTests(unittest.TestCase):
    def test_future_outcomes_do_not_leak(self):
        first=fight(1,"2025-01-01T12:00:00Z")
        future=fight(2,"2027-01-01T12:00:00Z",w="B",l="A")
        base=features([first],"2026-01-01T00:00:00Z")
        more=features([future,first],"2026-01-01T00:00:00Z")
        self.assertEqual(base,more)
        self.assertFalse(base["bet_eligible"])
    def test_recency_and_small_sample_flags(self):
        a=features([fight(1,"2024-01-01T12:00:00Z")],"2026-01-01T00:00:00Z")
        fighter=next(f for f in a["fighters"] if f["fighter"]=="A")
        self.assertTrue(fighter["inactivity_warning"])
        self.assertTrue(fighter["low_sample_warning"])
    def test_duplicates_are_removed(self):
        r=fight(1,"2025-01-01T12:00:00Z")
        a=features([r,r],"2026-01-01T00:00:00Z")
        self.assertEqual(a["fighters"][0]["historical_bouts"],1)
    def test_timezone_required(self):
        with self.assertRaises(ValueError):features([],"2026-01-01T00:00:00")
if __name__=="__main__":unittest.main()
