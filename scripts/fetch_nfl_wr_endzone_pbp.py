#!/usr/bin/env python3
"""Derive end-zone pass targets from nflverse play-by-play.
A target is counted only when receiver_player_id is verified and
air_yards >= yardline_100; this is a geometric estimate, not charted EZ data.
"""
import argparse,csv,collections,gzip,io,math,pathlib,urllib.request
URL="https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.csv.gz"
def derive(rows,season):
 counts=collections.Counter();team_counts=collections.Counter();seen=set()
 for r in rows:
  if str(r.get('season'))!=str(season) or str(r.get('season_type','REG')).upper()!='REG':continue
  pid=(r.get('receiver_player_id') or '').strip()
  team=(r.get('posteam') or '').strip().upper()
  week=(r.get('week') or '').strip()
  play=(r.get('play_id') or '').strip()
  game=(r.get('game_id') or '').strip()
  if not pid or not team or not week or not game or not play:continue
  if str(r.get('pass_attempt','')).strip() not in ('1','1.0'):continue
  try:
   air=float(r.get('air_yards',''));distance=float(r.get('yardline_100',''))
   if not math.isfinite(air) or not math.isfinite(distance) or distance<=0:continue
  except (TypeError,ValueError):continue
  if air<distance:continue
  k=(game,play)
  if k in seen:raise SystemExit('Duplicate PBP game/play key')
  seen.add(k)
  counts[(str(season),week,team,pid)]+=1
  team_counts[(str(season),week,team)]+=1
 return counts,team_counts
def main():
 p=argparse.ArgumentParser();p.add_argument('--season',type=int,default=2026);p.add_argument('--output',default='tmp/nfl_wr_endzone_pbp.csv');a=p.parse_args()
 req=urllib.request.Request(URL.format(season=a.season),headers={'User-Agent':'KSL-WR-Opportunity/1.0'})
 with urllib.request.urlopen(req,timeout=90) as response:raw=response.read(90_000_000)
 rows=csv.DictReader(io.StringIO(gzip.decompress(raw).decode('utf-8-sig')))
 counts,teams=derive(rows,a.season)
 if not counts:raise SystemExit('No verified end-zone PBP target events')
 out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=['season','week','team','player_id','end_zone_targets','team_end_zone_targets'])
  writer.writeheader()
  for (season,week,team,pid),n in sorted(counts.items()):
   writer.writerow(dict(season=season,week=week,team=team,player_id=pid,end_zone_targets=n,team_end_zone_targets=teams[(season,week,team)]))
 print('Derived',sum(counts.values()),'end-zone pass targets across',len(counts),'player-week records')
if __name__=='__main__':main()
