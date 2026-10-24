import tempfile
import unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from scripts.ufc_forecast_ledger import append_forecasts

class TestLedger(unittest.TestCase):
    def row(self):
        now=datetime.now(timezone.utc)
        return {"fight_id":"sample","fight_time":(now+timedelta(days=1)).isoformat(),
                "prediction_time":(now-timedelta(minutes=1)).isoformat(),
                "model_version":"research-v1","predicted_red_win":"0.55"}
    def test_append_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"ledger.csv"
            self.assertEqual(append_forecasts(p,[self.row()]),1)
            with self.assertRaises(ValueError):append_forecasts(p,[self.row()])
            self.assertEqual(len(p.read_text().splitlines()),2)
    def test_rejects_post_start(self):
        row=self.row();row["prediction_time"]=row["fight_time"]
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):append_forecasts(Path(folder)/"ledger.csv",[row])
    def test_rejects_nonfinite(self):
        row=self.row();row["predicted_red_win"]="nan"
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):append_forecasts(Path(folder)/"ledger.csv",[row])

if __name__=="__main__":unittest.main()
