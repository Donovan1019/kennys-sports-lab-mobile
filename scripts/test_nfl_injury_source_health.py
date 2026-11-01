#!/usr/bin/env python3
"""Tests for official NFL injury-source probe; network calls are mocked."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import check_nfl_official_injuries as mod

class Response:
    status=200
    headers={'Content-Type':'text/html'}
    def __init__(self,url):self.url=url
    def geturl(self):return self.url
    def read(self,n):return b'<html>Injury reports</html>'
    def __enter__(self):return self
    def __exit__(self,*args):return False

class ProbeTests(unittest.TestCase):
    def run_probe(self,url):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(mod,'DEST',Path(tmp)/'health.json'),patch.object(mod.urllib.request,'urlopen',return_value=Response(url)):
                mod.main()
                return json.loads(mod.DEST.read_text())
    def test_official_domain(self):
        record=self.run_probe('https://www.nfl.com/injuries/')
        self.assertTrue(record['source_reachable'])
        self.assertEqual(record['verified_player_reports'],0)
    def test_redirect_to_untrusted_domain(self):
        record=self.run_probe('https://fake-nfl.example/injuries/')
        self.assertFalse(record['source_reachable'])
        self.assertEqual(record['ingestion_status'],'UNAVAILABLE')
if __name__=='__main__':unittest.main()
