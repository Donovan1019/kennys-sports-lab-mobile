#!/usr/bin/env python3
"""Collect independent ESPN final scores for archived model events.

A verified final score is NOT Kalshi contract settlement verification.
Never mark settlement_verified from ESPN alone.
"""
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'data/kalshi-pregame-forecasts.json'
LEAGUES={'basketball_nba':('basketball','nba'),
         'americanfootball_nfl':('football','nfl'),
         'icehockey_nhl':('hockey','nhl'),
         'basketball_ncaab':('basketball','mens-college-basketball')}
def norm(value):return re.sub(r'[^a-z0-9]','',str(value or '').lower())
def dt(value):
 try:return datetime.fromisoformat(value.replace('Z','+00:00'))
 except (ValueError,AttributeError):return None
def get_scores(sport,date):
 group,league=LEAGUES[sport]
 url=f'https://site.api.espn.com/apis/site/v2/sports/{group}/{league}/scoreboard?'+urlencode({'dates':date})
 with urlopen(Request(url,headers={'User-Agent':'KennysSportsLab/1.0','Accept':'application/json'}),timeout=18) as r:
  return json.load(r).get('events',[])
def collect():
 if not ARCHIVE.exists():
  print('No archived forecasts yet');return
 archive=json.loads(ARCHIVE.read_text());rows=archive.get('observations',[])
 now=datetime.now(timezone.utc);cache={};updated=0;failed=[]
 for row in rows:
  if row.get('game_result_verified'):continue
  start=dt(row.get('game_start_at'));sport=row.get('sport')
  if sport not in LEAGUES or not start or start>=now-timedelta(hours=3):continue
  event=str(row.get('event') or '')
  teams=re.split(r'\s+@\s+',event)
  if len(teams)!=2:continue
  key=(sport,start.strftime('%Y%m%d'))
  if key not in cache:
   try:cache[key]=get_scores(*key)
   except Exception as exc:cache[key]=[];failed.append(f'{key}: {type(exc).__name__}')
  for game in cache[key]:
   competitors=(game.get('competitions') or [{}])[0].get('competitors') or []
   if len(competitors)!=2:continue
   names=[c.get('team',{}).get('displayName') for c in competitors]
   if {norm(n) for n in names}!={norm(t) for t in teams}:continue
   state=game.get('status',{}).get('type',{})
   if not state.get('completed') or state.get('name') not in ('STATUS_FINAL','STATUS_FINAL_OT','STATUS_FINAL_SO'):continue
   if any(c.get('score') is None for c in competitors):continue
   scores=[int(c['score']) for c in competitors]
   if scores[0]==scores[1]:continue
   winner=names[0] if scores[0]>scores[1] else names[1]
   if norm(row.get('selection')) not in {norm(n) for n in names}:continue
   row['game_result_verified']=True
   row['game_result_source']='ESPN public scoreboard'
   row['game_result_event_id']=game.get('id')
   row['game_result_winner']=winner
   row['game_result_checked_at']=now.isoformat()
   row['game_result_outcome']=int(norm(row['selection'])==norm(winner))
   # Explicitly DO NOT set actual_outcome/settlement_verified.
   updated+=1;break
 if updated:
  ARCHIVE.write_text(json.dumps(archive,indent=2)+'\n')
 print(f'Independent completed-game results matched: {updated}; total verified game results: '+str(sum(bool(r.get('game_result_verified')) for r in rows)))
 if failed:print('Scoreboard lookup failures: '+'; '.join(sorted(set(failed))))
if __name__=='__main__':collect()
