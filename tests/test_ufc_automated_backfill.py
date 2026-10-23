import datetime as dt
import unittest
from scripts.ufc_automated_backfill import select_days,run
TODAY=dt.date(2026,10,23)
def fetch(day):return {"events":[]}
class UFCAutomatedBackfillTests(unittest.TestCase):
    def test_first_batch_and_recent_days(self):
        days=select_days({},TODAY)
        self.assertIn(dt.date(2024,1,1),days)
        self.assertIn(dt.date(2026,10,22),days)
        self.assertLessEqual(len(days),97)
        self.assertEqual(len(days),97)
    def test_resume_skips_completed_old_days(self):
        completed={"successful_days":["2024-01-01","2024-01-02"]}
        days=select_days(completed,TODAY)
        self.assertIn(dt.date(2024,1,3),days)
        self.assertNotIn(dt.date(2024,1,1),days)
    def test_repeat_does_not_duplicate_checkpoint(self):
        result=run({},TODAY,fetch)
        repeated=run(result,TODAY,fetch)
        self.assertEqual(len(repeated["successful_days"]),len(set(repeated["successful_days"])))
        self.assertFalse(repeated["bet_eligible"])
if __name__=="__main__":unittest.main()
