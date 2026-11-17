import json
import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import audit_kalshi_integrity as audit

class Tests(unittest.TestCase):
 def test_evidence(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'data').mkdir()
   record=dict(event_id='a',selection='Home',model_source='model',forecast_at='2026-11-17T01:00:00Z',game_start_at='2026-11-17T03:00:00Z',predicted_probability=.8,actual_outcome=1,settlement_verified=False,settlement_source='official')
   path=root/'data/kalshi-pregame-forecasts.json'
   with patch.object(audit,'ROOT',root):
    path.write_text(json.dumps({'observations':[record]}))
    self.assertEqual(audit.audit(datetime(2026,11,17,12,tzinfo=timezone.utc))['verified_historical_outcomes'],0)
    record['settlement_verified']=True
    path.write_text(json.dumps({'observations':[record,record]}))
    result=audit.audit(datetime(2026,11,17,12,tzinfo=timezone.utc))
    self.assertEqual(result['verified_historical_outcomes'],1)
    self.assertAlmostEqual(result['historical_brier_score'],.04)
    self.assertEqual(result['diamond_issuance'],'BLOCKED')
    record['forecast_at']='2026-11-17T04:00:00Z'
    path.write_text(json.dumps({'observations':[record]}))
    self.assertEqual(audit.audit(datetime(2026,11,17,12,tzinfo=timezone.utc))['verified_historical_outcomes'],0)
if __name__=='__main__':unittest.main()
