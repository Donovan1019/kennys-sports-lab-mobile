import unittest
from scripts.ufc_verified_stats_enrich import enrich, verified_stats

def fighter(name):
    return {"name":name,"source":"licensed-feed","source_record_id":name,
            "source_permission_verified":True,"stats_verified":True,
            "verified_at":"2026-10-23T00:00:00Z","sample_size":12,
            "ko_rate":0.5,"submission_rate":0.25,"decision_rate":0.25}

class TestUFCStatsEnrichment(unittest.TestCase):
    def test_reject_unlicensed(self):
        self.assertIsNone(verified_stats({**fighter("A"),"source_permission_verified":False}))
        with self.assertRaises(ValueError):
            enrich({"fights":[]},{"fighters":[]})
    def test_reject_incomplete_and_duplicate(self):
        self.assertIsNone(verified_stats({**fighter("A"),"sample_size":2}))
        with self.assertRaises(ValueError):
            enrich({"fights":[]},{"source_permission_verified":True,"fighters":[fighter("A"),fighter("A")]})
    def test_enrich_but_never_bet_eligible(self):
        card={"fights":[{"id":"1","red":"A","blue":"B","scheduled_rounds":3,"fighter_status_verified":True}]}
        data=enrich(card,{"source_permission_verified":True,"fighters":[fighter("A"),fighter("B")]})
        self.assertEqual(data["blocked"],[])
        self.assertTrue(data["fights"][0]["stats_verified"])
        self.assertFalse(data["fights"][0]["bet_eligible"])
        self.assertFalse(data["bet_eligible"])
    def test_missing_rounds_remain_blocked(self):
        card={"fights":[{"id":"1","red":"A","blue":"B","scheduled_rounds":None}]}
        data=enrich(card,{"source_permission_verified":True,"fighters":[fighter("A"),fighter("B")]})
        self.assertTrue(data["blocked"])
if __name__=="__main__":
    unittest.main()
