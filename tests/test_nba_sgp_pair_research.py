import unittest
from scripts.nba_sgp_pair_research import evaluate
class SameGamePairs(unittest.TestCase):
    def test_same_game_join_not_cross_game(self):
        data={"source":"espn-public-boxscore","sport":"nba","players":[
          {"id":"a","games":[{"game_id":"1","values":{"Points":25}},{"game_id":"2","values":{"Points":25}}]},
          {"id":"b","games":[{"game_id":"1","values":{"Points":21}}]},
          {"id":"c","games":[{"game_id":"3","values":{"Points":24}}]}]}
        result=evaluate(data)
        self.assertFalse(result["promotion_approved"])
        self.assertEqual(result["status"],"research_only")
        self.assertEqual(result["markets"],{})
    def test_pairs_are_not_independent_samples(self):
        games=[{"game_id":str(i),"values":{"Points":25}} for i in range(100)]
        data={"source":"espn-public-boxscore","sport":"nba","players":[
            {"id":"a","games":games},{"id":"b","games":games},{"id":"c","games":games}]}
        result=evaluate(data)["markets"]["Points"]
        self.assertEqual(result["observed_player_pairs"],300)
        self.assertEqual(result["distinct_games"],100)
        self.assertEqual(result["max_pairs_in_single_game"],3)
        self.assertFalse(result["independent_sample_size_claim"])

    def test_reject_unverified(self):
        with self.assertRaises(ValueError):evaluate({"source":"unverified","sport":"nba"})
if __name__=="__main__":unittest.main()
