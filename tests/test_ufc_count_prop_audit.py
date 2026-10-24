import unittest
from scripts.ufc_count_prop_audit import audit,poisson_tail
class CountPropAuditTests(unittest.TestCase):
    def test_poisson(self):
        self.assertAlmostEqual(poisson_tail(1,.5),1-__import__('math').exp(-1))
        self.assertEqual(poisson_tail(0,.5),0)
    def test_prior_date_only_and_no_betting_claim(self):
        def row(fid,day,count):
            return dict(fight_id=fid,fighter_id="A",fight_time=day+"T00:00:00Z",
                settled="true",active_seconds="300",sig_landed=str(count),
                sig_attempted=str(count+10),takedowns_landed="1",takedowns_attempted="2")
        rows=[row("1","2025-01-01",10),row("2","2025-01-02",20),
              row("3","2025-01-03",30),row("4","2025-01-04",40),
              row("5","2025-01-04",100)]
        out=audit(rows,min_prior=3)
        self.assertEqual(out["markets"]["sig_landed"]["n"],2)
        self.assertFalse(out["bet_eligible"])
        self.assertFalse(out["predictive_duration_available"])
        self.assertGreater(out["markets"]["sig_landed"]["mae"],0)
if __name__=="__main__":unittest.main()
