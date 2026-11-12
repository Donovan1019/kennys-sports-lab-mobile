import unittest
from scripts.nfl_roster_crosscheck import assess, normalize, participants, roster_names

class NFLRosterCrosscheckTests(unittest.TestCase):
    def test_name_normalization_and_roster_shape(self):
        self.assertEqual(normalize("D'Andre Swift"),"dandreswift")
        payload={"athletes":[{"items":[{"athlete":{"fullName":"D'Andre Swift"}}]}]}
        self.assertIn("dandreswift",roster_names(payload))
    def test_fail_closed_and_game_participants(self):
        self.assertEqual(participants("New England Patriots @ Chicago Bears"),("New England Patriots","Chicago Bears"))
        props={"odds":[{"event":"New England Patriots @ Chicago Bears","player":"Player A"},
                       {"event":"New England Patriots @ Chicago Bears","player":"Player B"},
                       {"event":"New England Patriots @ Chicago Bears","player":"Player C"},
                       {"event":"Unknown game","player":"Player D"}]}
        rosters={"New England Patriots":{"playera","playerc"},
                 "Chicago Bears":{"playerc"}}
        result=assess(props,rosters)
        counts=result["counts"]
        self.assertEqual(counts["roster_listed_quotes"],1)
        self.assertEqual(counts["not_listed_quotes"],1)
        self.assertEqual(counts["ambiguous_player_quotes"],1)
        self.assertEqual(counts["unverifiable_quotes"],1)
        self.assertEqual(result["verified_betting_recommendations"],0)
        self.assertFalse(result["lineup_verified"])
    def test_unavailable_roster_does_not_claim_nonlisting(self):
        props={"odds":[{"event":"New England Patriots @ Chicago Bears","player":"Player A"}]}
        result=assess(props,{"Chicago Bears":{"playera"}},["New England Patriots"])
        self.assertEqual(result["counts"]["unverifiable_quotes"],1)
        self.assertEqual(result["counts"]["roster_listed_quotes"],0)

if __name__=="__main__":unittest.main()
