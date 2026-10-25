import unittest
from scripts.fetch_nfl_stats import parse

class NFLImporterTests(unittest.TestCase):
    def test_player_display_name_schema(self):
        csv_data=("season,week,season_type,player_id,player_display_name,recent_team,position,receiving_yards,receptions\n"
                  "2025,1,REG,p1,Test Receiver,ABC,WR,81,6\n")
        result=parse(csv_data)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["values"]["Receiving yards"],81.0)
        self.assertEqual(result[0]["values"]["Receptions"],6.0)

    def test_alternate_name_team_and_partial_stats(self):
        csv_data=("season,week,season_type,player_id,player_name,team,position,rushing_yards\n"
                  "2026,2,REG,p2,Test Runner,XYZ,RB,54\n")
        result=parse(csv_data)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["team"],"XYZ")
        self.assertEqual(result[0]["values"],{"Rushing yards":54.0})

    def test_reject_missing_identity(self):
        with self.assertRaises(ValueError):
            parse("season,week,season_type,receiving_yards\n2026,1,REG,50\n")

    def test_skip_invalid_or_non_game_rows(self):
        csv_data=("season,week,season_type,player_id,player_display_name,recent_team,position,receiving_yards\n"
                  "2026,1,REG,p1,Receiver,ABC,WR,30\n"
                  "2026,2,PRE,p1,Receiver,ABC,WR,70\n"
                  "2026,3,REG,p1,Receiver,ABC,WR,invalid\n")
        result=parse(csv_data)
        self.assertEqual(len(result),1)

if __name__=="__main__":
    unittest.main()
