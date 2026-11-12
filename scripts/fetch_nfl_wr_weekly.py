#!/usr/bin/env python3
"""Fetch 2026 nflverse weekly CSV and normalize columns for WR shares.
Public source: nflverse/nflverse-data release stats_player. Fail closed.
"""
import csv,io,sys,urllib.request,pathlib
URL='https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2026.csv'
def main():
 req=urllib.request.Request(URL,headers={'User-Agent':'KSL-WR-Opportunity/1.0'})
 with urllib.request.urlopen(req,timeout=45) as r:
  raw=r.read(25_000_000)
 rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
 if not rows:raise SystemExit('Upstream weekly stats CSV empty')
 required={'player_id','season','week','targets','position'}
 if not required.issubset(rows[0]):raise SystemExit('Upstream schema missing: '+str(required-set(rows[0])))
 normalized=[]
 for r in rows:
  if str(r.get('season'))!='2026':continue
  name=r.get('player_display_name') or r.get('player_name') or r.get('player_id')
  team=r.get('recent_team') or r.get('team')
  if not team:continue
  normalized.append(dict(r,player_name=name,recent_team=team))
 if len(normalized)<100:raise SystemExit('Upstream 2026 coverage unexpectedly small')
 dest=pathlib.Path('tmp/nfl_wr_2026_weekly.csv');dest.parent.mkdir(exist_ok=True)
 with dest.open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(normalized[0]));writer.writeheader();writer.writerows(normalized)
 print('Fetched',len(normalized),'2026 player-week rows')
if __name__=='__main__':main()
