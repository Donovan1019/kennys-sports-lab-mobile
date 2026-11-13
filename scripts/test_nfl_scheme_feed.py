import unittest
from scripts.validate_nfl_scheme_feed import validate

BASE = {"source":"licensed-charting", "generated_at":"2026-11-13T10:00:00Z", "rows":[{"event_id":"abc","team":"NYG","side":"home","coverage":"zone","snaps":30,"opportunities":50,"verified":True,"source_url":"https://example.com/chart"}]}

class TestScheme(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(len(validate(BASE)["rows"]),1)
    def test_no_fabrication(self):
        for key,value in [("verified",False),("snaps",51),("coverage","guess")]:
            import copy
            x=copy.deepcopy(BASE);x["rows"][0][key]=value
            with self.assertRaises(ValueError): validate(x)
    def test_duplicate(self):
        import copy
        x=copy.deepcopy(BASE);x["rows"].append(copy.deepcopy(x["rows"][0]))
        with self.assertRaises(ValueError):validate(x)

if __name__=="__main__": unittest.main()
