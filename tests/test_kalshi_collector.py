import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import collect_kalshi as collector

class CollectorTests(unittest.TestCase):
 def test_partial_failure_preserves_successful_series(self):
  with tempfile.TemporaryDirectory() as tmp:
   market={'ticker':'KXNBAGAME-26NOV20TEST-AAA','event_ticker':'KXNBAGAME-26NOV20TEST','title':'Example wins','status':'active','close_time':'2026-11-25T22:00:00Z','yes_ask_dollars':'0.55'}
   def fetch(series):
    if series=='KXNHLGAME':raise RuntimeError('temporary outage')
    return [market] if series=='KXNBAGAME' else []
   with patch.object(collector,'fetch',side_effect=fetch),patch.object(collector,'Path',wraps=Path):
    import os
    previous=os.getcwd()
    try:
     os.chdir(tmp)
     collector.main()
     result=json.loads(Path('data/kalshi-markets.json').read_text())
    finally:os.chdir(previous)
   self.assertTrue(result['partial_failure'])
   self.assertEqual(len(result['series_failed']),1)
   self.assertIn('KXNBAGAME',result['series_successful'])
   self.assertGreaterEqual(result['series_checked'],1)
 def test_all_series_fail_preserves_previous_file(self):
  with tempfile.TemporaryDirectory() as tmp:
   import os
   previous=os.getcwd()
   try:
    os.chdir(tmp)
    Path('data').mkdir()
    Path('data/kalshi-markets.json').write_text('{"old":true}')
    with patch.object(collector,'fetch',side_effect=RuntimeError('outage')):
     with self.assertRaises(SystemExit):collector.main()
    self.assertEqual(json.loads(Path('data/kalshi-markets.json').read_text()),{'old':True})
   finally:os.chdir(previous)
if __name__=='__main__':unittest.main()
