import json
import pathlib
import re
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class UFCTabTests(unittest.TestCase):
    def test_navigation_on_all_sports(self):
        for page in ('index.html','nfl.html','nba.html','nhl.html','ufc.html'):
            html=(ROOT/page).read_text()
            self.assertIn('href="./ufc.html"',html,page)
    def test_ufc_research_feed_is_not_fake(self):
        payload=json.loads((ROOT/'feed/ufc_research.json').read_text())
        self.assertEqual(payload['sport'],'UFC')
        self.assertFalse(payload['bet_eligible'])
        self.assertEqual(payload['fights'],[])
    def test_modules_and_scripts_exist(self):
        html=(ROOT/'ufc.html').read_text()
        for marker in ('ufc-event-status','ufc-fights','ufc-top-plays','ufc-fighter-select','ufc-markets','ufc-builders','ufc-integrity','ufc_lab.js','ufc_lab.css'):
            self.assertIn(marker,html)
        js=(ROOT/'ufc_lab.js').read_text()
        self.assertIn('UNAVAILABLE',js)
        self.assertIn('research',js.lower())

if __name__=='__main__':unittest.main()
