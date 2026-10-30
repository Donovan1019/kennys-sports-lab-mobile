import datetime as dt
import unittest
from scripts.simulate_nba_ml import build

NOW=dt.datetime(2026,10,30,20,tzinfo=dt.timezone.utc)
def fixture():
    t="2026-10-30T20:00:00+00:00"
    odds={"status":"ok","fetched_at":t,"odds":[]}
    model={"status":"validated","calibration_passed":True,"generated_at":t,"predictions":[]}
    for i in range(5):
        eid="game"+str(i);a="Away"+str(i);h="Home"+str(i)
        model["predictions"] += [{"event_id":eid,"team":h,"win_probability":.75},{"event_id":eid,"team":a,"win_probability":.25}]
        for team,price in ((h,-200),(a,180)):
            odds["odds"].append({"market":"h2h","event_id":eid,"event":a+" @ "+h,"selection":team,"price":price,"bookmaker":"draftkings","commence_time":"2026-10-31T00:00:00+00:00","updated_at":t})
    return odds,model
class TestSimulation(unittest.TestCase):
    def test_reproducible_and_fail_closed(self):
        odds,model=fixture();a=build(odds,model,{"checks":{}},NOW,1000);b=build(odds,model,{"checks":{}},NOW,1000)
        self.assertEqual(a,b);self.assertEqual(len(a["games"]),10);self.assertEqual(len(a["parlays"]),4)
        self.assertTrue(all(not p["betting_eligible"] for p in a["parlays"]))
        self.assertTrue(all(len(set(x["event_id"] for x in p["legs"]))==len(p["legs"]) for p in a["parlays"]))
        self.assertTrue(all(p["bookmaker"]=="draftkings" for p in a["parlays"]))
    def test_stale_fails_closed(self):
        odds,model=fixture();odds["fetched_at"]="2026-10-01T00:00:00+00:00"
        self.assertEqual(build(odds,model,{},NOW)["status"],"unavailable")
    def test_invalid_model_fails_closed(self):
        odds,model=fixture();model["calibration_passed"]=False
        self.assertEqual(build(odds,model,{},NOW)["games"],[])
if __name__=="__main__":unittest.main()
