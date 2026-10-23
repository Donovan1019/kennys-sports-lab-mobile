import datetime as dt
import importlib.util
import pathlib
import unittest

path=pathlib.Path(__file__).resolve().parents[1]/'scripts'/'export_three_sport_predictions.py'
spec=importlib.util.spec_from_file_location('export_predictions',path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ForecastTests(unittest.TestCase):
    def test_timestamp_requires_timezone(self):
        self.assertIsNone(module.stamp('2026-10-23T12:00:00'))
        self.assertIsNotNone(module.stamp('2026-10-23T12:00:00Z'))
    def test_no_predictions_for_completed_games(self):
        now=dt.datetime(2030,1,1,tzinfo=dt.timezone.utc)
        for sport in module.SPORTS:
            self.assertEqual(module.model(sport,now),[])
    def test_no_future_dated_data_or_missing_history(self):
        now=dt.datetime(2026,10,23,tzinfo=dt.timezone.utc)
        for sport in module.SPORTS:
            for row in module.model(sport,now):
                self.assertLess(module.stamp(row['prediction_created_at']),module.stamp(row['commence_time']))
                self.assertFalse(row['bet_eligible'])
                self.assertTrue(row['research_only'])

if __name__=='__main__':unittest.main()
