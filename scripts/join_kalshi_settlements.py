#!/usr/bin/env python3
"""Join archived pregame forecasts to independently observed game results and Kalshi settlements.
Only matching contract and game outcomes qualify for calibration.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'data/kalshi-pregame-forecasts.json'
SETTLEMENTS=ROOT/'data/kalshi-settlements.json'

def join():
 if not ARCHIVE.exists() or not SETTLEMENTS.exists():
  print('No archive/settlement file; preserving evidence');return
 archive=json.loads(ARCHIVE.read_text())
 settlements=json.loads(SETTLEMENTS.read_text()).get('settlements',{})
 joined=0;conflicts=0
 for r in archive.get('observations',[]):
  if r.get('settlement_verified'):continue
  ticker=r.get('kalshi_ticker')
  m=settlements.get(ticker) if ticker else None
  if not m or m.get('result') not in ('yes','no') or m.get('status') not in ('settled','finalized'):continue
  if r.get('kalshi_match_status')!='UNIQUE' or r.get('game_result_verified') is not True:continue
  if not m.get('event_ticker') or not ticker.startswith(m['event_ticker']+'-'):continue
  outcome=int(m['result']=='yes')
  if outcome!=r.get('game_result_outcome'):
   conflicts+=1
   r['settlement_conflict']='Kalshi settlement disagrees with independent final score'
   continue
  r['actual_outcome']=outcome
  r['settlement_verified']=True
  r['settlement_source']='Kalshi public settled market API + ESPN final score'
  joined+=1
 if joined or conflicts:ARCHIVE.write_text(json.dumps(archive,indent=2)+'\n')
 print(f'Independent contract settlements joined: {joined}; conflicting results: {conflicts}')
if __name__=='__main__':join()
