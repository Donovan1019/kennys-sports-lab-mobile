import unittest
from scripts.ufc_camp_features import camp_features
CUTOFF="2026-10-23T10:00:00Z"
def row():
    return {"fight_id":"1","fighter":"A","gym":"Gym X","source_url":"https://example.org/report",
            "verified_at":"2026-10-22T10:00:00Z","camp_days":60,
            "gym_changed":False,"head_coach_continuity":True,"short_notice":False}
class UFCCampFeaturesTests(unittest.TestCase):
    def test_valid_record_research_only(self):
        r=camp_features([row()],CUTOFF)
        self.assertEqual(r["accepted"],1)
        self.assertFalse(r["bet_eligible"])
        self.assertIsNone(r["gym_advantage_probability"])
    def test_post_fight_or_post_cutoff_leakage_blocked(self):
        x=row();x["verified_at"]="2026-10-24T10:00:00Z"
        self.assertEqual(camp_features([x],CUTOFF)["accepted"],0)
    def test_duplicate_camp_blocked(self):
        r=camp_features([row(),row()],CUTOFF)
        self.assertEqual(r["accepted"],1)
        self.assertEqual(r["rejected"],1)
    def test_unknown_fields_are_not_assumed_false(self):
        x=row();x["short_notice"]=None;x["camp_days"]=None
        r=camp_features([x],CUTOFF)
        self.assertEqual(r["records"][0]["camp_completeness"],.5)
if __name__=="__main__":unittest.main()
