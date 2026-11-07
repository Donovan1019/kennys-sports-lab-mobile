import unittest
from scripts.ufc_join_all_stats import join
class JoinedUFCTests(unittest.TestCase):
    def test_all_existing_stats_joined_without_false_bet_certification(self):
        card={"fights":[{"id":"42","red":"José Souza","blue":"Blue Fighter","scheduled_rounds":None}]}
        mirror={"fighters":[{"name":"José Souza","status":"INSUFFICIENT_OR_AMBIGUOUS"},{"name":"Blue Fighter","status":"MATCHED_HISTORICAL_STATS","career_round_totals":{"round_rows":8,"sig_landed":30}}]}
        elo={"projections":[{"fight_id":"42","red":"José Souza","blue":"Blue Fighter","red_elo":1500,"blue_elo":1520}]}
        unified={"fights":[{"fight_id":"42","count_simulation":{"Blue Fighter":{"status":"UNAVAILABLE","historical_per_round":{"sig_landed":3.75}}},"sparse_data_probability":{"red":0.48,"blue":0.52}}]}
        legacy={"blocked":[{"fight_id":"42","reason":"Missing fighter stats: red"}]}
        result=join(card,mirror,elo,unified,legacy)
        self.assertEqual(result["coverage"]["fighter_sides_with_historical_stats"],1)
        self.assertEqual(result["coverage"]["paired_elo_matchups"],1)
        self.assertIsNone(result["fights"][0]["fighters"]["red"]["historical_career_round_totals"])
        self.assertEqual(result["fights"][0]["fighters"]["blue"]["unified_count_research"]["historical_per_round"]["sig_landed"],3.75)
        self.assertFalse(result["bet_eligible"])
        self.assertIsNone(result["fights"][0]["model_ev"])
if __name__ == "__main__": unittest.main()
