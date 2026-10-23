import datetime as dt
import importlib.util
import pathlib
import tempfile
import unittest

FILE=pathlib.Path(__file__).resolve().parents[1]/'scripts'/'three_sport_backtest.py'
spec=importlib.util.spec_from_file_location('backtest',FILE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class BacktestTests(unittest.TestCase):
    def test_stamp_utc(self):
        self.assertEqual(m.stamp('2026-10-22T20:00:00Z').hour,20)
    def test_snapshot_immutable(self):
        with tempfile.TemporaryDirectory() as d:
            old=m.ROOT
            try:
                m.ROOT=pathlib.Path(d)
                (m.ROOT/'feed').mkdir()
                t=dt.datetime(2026,10,22,12,tzinfo=dt.timezone.utc)
                first=m.capture(t)
                second=m.capture(t)
                self.assertEqual(first['NFL']['status'],'captured')
                self.assertEqual(second['NFL']['status'],'immutable_existing')
            finally:m.ROOT=old
    def test_unverified_predictions_are_not_wins(self):
        with tempfile.TemporaryDirectory() as d:
            old=m.ROOT
            try:
                m.ROOT=pathlib.Path(d)
                self.assertEqual(m.grade('2026-10-22')['summary']['verified_picks'],0)
                self.assertIsNone(m.grade('2026-10-22')['summary']['roi'])
            finally:m.ROOT=old

if __name__=='__main__':unittest.main()
