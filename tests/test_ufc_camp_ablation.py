import unittest
from scripts.ufc_camp_ablation import audit
def pair(fid="1",base=.5,camp=.7):
    return {"fight_id":fid,"start_time":"2026-10-23T20:00:00Z",
      "baseline_generated_at":"2026-10-23T10:00:00Z","camp_generated_at":"2026-10-23T10:00:00Z",
      "camp_verified_at":"2026-10-22T10:00:00Z","holdout_verified":True,"camp_source_verified":True,
      "baseline_model_version":"elo-v1","camp_model_version":"camp-v1","red_won":True,
      "baseline_red_probability":base,"camp_red_probability":camp}
class UFCCampAblationTests(unittest.TestCase):
    def test_paired_comparison_and_no_approval(self):
        r=audit([pair("1"),pair("2")],iterations=100,min_pairs=1)
        self.assertEqual(r["paired_fights"],2)
        self.assertGreater(r["improvement"],0)
        self.assertFalse(r["bet_eligible"])
    def test_rejects_future_sourced_camp(self):
        x=pair();x["camp_verified_at"]="2026-10-23T11:00:00Z"
        self.assertEqual(audit([x])["paired_fights"],0)
    def test_rejects_duplicate(self):
        r=audit([pair(),pair()])
        self.assertEqual(r["paired_fights"],1)
        self.assertEqual(len(r["rejected"]),1)
    def test_missing_holdout_blocks(self):
        x=pair();x["holdout_verified"]=False
        self.assertEqual(audit([x])["paired_fights"],0)
if __name__=="__main__":unittest.main()
