import unittest
from scripts.ufc_winner_history import summarize_winners
def fight(fid="1",method=None):
    return {"event_id":"e","fight_id":fid,"winner":"A","loser":"B","method":method,
            "winner_verified":True,"method_verified":False}
class UFCWinnerHistoryTests(unittest.TestCase):
    def test_method_missing_does_not_remove_winner(self):
        result=summarize_winners([fight(),fight(),fight("2")])
        self.assertEqual(result["unique_completed_fights"],2)
        a=next(f for f in result["fighters"] if f["name"]=="A")
        self.assertEqual(a["wins"],2)
        self.assertFalse(result["method_probabilities_available"])
        self.assertFalse(result["bet_eligible"])
    def test_unverified_winner_rejected(self):
        bad=fight()
        bad["winner_verified"]=False
        self.assertEqual(summarize_winners([bad])["unique_completed_fights"],0)
if __name__=="__main__":unittest.main()
