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
    def test_reject_unverified(self):
        with self.assertRaises(ValueError):evaluate({"source":"unverified","sport":"nba"})
if __name__=="__main__":unittest.main()
