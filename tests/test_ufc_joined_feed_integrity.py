"""Cross-feed UFC identity and research readiness invariants."""
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"feed"
def read(name):return json.loads((ROOT/name).read_text())
class JoinedFeedIntegrityTests(unittest.TestCase):
    def test_joined_feed_matches_card_and_source_research(self):
        card=read("ufc_research.json")
        joined=read("ufc_joined_stats.json")
        unified=read("ufc_unified_research.json")
        mirror=read("ufc_fighter_stats_mirror.json")
        elo=read("ufc_elo_projections.json")
        expected={str(f["id"]):(f["red"],f["blue"]) for f in card["fights"]}
        actual={str(f["fight_id"]):(f["red"],f["blue"]) for f in joined["fights"]}
        self.assertEqual(expected,actual)
        self.assertEqual(len(actual),len(joined["fights"]))
        self.assertEqual(len(unified["fights"]),len(joined["fights"]))
        self.assertEqual(joined["coverage"]["fights"],len(actual))
        self.assertEqual(joined["coverage"]["fighter_sides_with_historical_stats"],sum(bool(side["historical_career_round_totals"]) for fight in joined["fights"] for side in fight["fighters"].values()))
        self.assertEqual(joined["coverage"]["paired_elo_matchups"],sum(fight["elo"] is not None for fight in joined["fights"]))
        self.assertEqual(joined["coverage"]["verified_scheduled_round_fights"],sum(fight["verified_scheduled_rounds"] in (3,5) for fight in joined["fights"]))
        self.assertFalse(joined["bet_eligible"])
        self.assertTrue(joined["research_only"])
        for fight in joined["fights"]:
            self.assertFalse(fight["bet_eligible"])
            self.assertIsNone(fight["model_ev"])
            for side in fight["fighters"].values():
                self.assertFalse(side["stats_asof_verified"] and side["historical_career_round_totals"] is None)
        self.assertEqual(len(mirror["fighters"]),2*len(card["fights"]))
        self.assertIsInstance(elo.get("projections"),list)
if __name__=="__main__":unittest.main()
