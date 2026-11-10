import importlib.util
import pathlib
import unittest

spec=importlib.util.spec_from_file_location("ncaab_player_import",pathlib.Path(__file__).with_name("ncaab_player_import.py"))
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class TestPlayerIdentity(unittest.TestCase):
    def test_source_id_over_name(self):
        rows=[{"canonical_player_id":"espn:1","provider_player_id":"1","player_name":"John Smith","team_id":"10","date":"2025-11-01"},
              {"canonical_player_id":"espn:2","provider_player_id":"2","player_name":"John Smith","team_id":"20","date":"2025-11-01"}]
        mapping=mod.build_map(rows)
        self.assertEqual(len(mapping["players"]),2)
        self.assertIn("johnsmith",mapping["ambiguous_name_aliases"])
        self.assertNotIn("johnsmith",mapping["unique_name_aliases"])
    def test_transfer_keeps_identity(self):
        rows=[{"canonical_player_id":"espn:1","provider_player_id":"1","player_name":"A Player","team_id":"10","date":"2025-11-01"},
              {"canonical_player_id":"espn:1","provider_player_id":"1","player_name":"A Player","team_id":"20","date":"2026-11-01"}]
        mapping=mod.build_map(rows)
        self.assertEqual(len(mapping["players"]),1)
        self.assertEqual(len(mapping["players"]["espn:1"]["team_history"]),2)
    def test_parse_source_ids(self):
        summary={"boxscore":{"players":[{"team":{"id":"5"},"statistics":[{"labels":["PTS","REB"],"athletes":[{"athlete":{"id":"123","displayName":"Test Player"},"stats":["15","7"]}]}]}]}}
        result=mod.parse(summary,"game1","2026-11-10")
        self.assertEqual(result[0]["canonical_player_id"],"espn:123")
        self.assertEqual(result[0]["statistics"]["PTS"],"15")
if __name__=="__main__":unittest.main()
