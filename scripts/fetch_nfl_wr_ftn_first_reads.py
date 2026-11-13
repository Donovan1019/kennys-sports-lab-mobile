#!/usr/bin/env python3
"""Verified FTN first-read target counts joined to nflverse play-by-play.
FTN charting CC BY-SA 4.0; retain attribution and avoid guessing unknown schemas.
"""
import argparse,collections,csv,gzip,io,pathlib,urllib.request
FTN="https://github.com/nflverse/nflverse-data/releases/download/ftn_charting/ftn_charting_{season}.csv"
PBP="https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.csv.gz"
def fetch(url,compressed=False):
 req=urllib.request.Request(url,headers={'User-Agent':'KSL-WR-Opportunity/1.0'})
 with urllib.request.urlopen(req,timeout=90) as r:raw=r.read(100_000_000)
 if compressed:raw=gzip.decompress(raw)
 return csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
def build(ftn,pbp,season):
 chart={}
 for r in ftn:
  if not {'game_id','play_id','read_thrown'}.issubset(r):raise SystemExit('FTN schema lacks game_id/play_id/read_thrown')
  key=((r.get('game_id') or '').strip(),(r.get('play_id') or '').strip())
  if not all(key):continue
  read=(r.get('read_thrown') or '').strip().upper()
  if key in chart:raise SystemExit('Duplicate FTN game/play: '+str(key))
  chart[key]=read
 if not chart:raise SystemExit('No FTN charting rows')
 counts=collections.Counter();team_counts=collections.Counter();seen=set();matched=0
 for r in pbp:
  if str(r.get('season'))!=str(season) or str(r.get('season_type','REG')).upper()!='REG':continue
  key=((r.get('game_id') or '').strip(),(r.get('play_id') or '').strip())
  if key not in chart:continue
  matched+=1
  if chart[key] not in ('0','0.0','DES'):continue
  if str(r.get('pass_attempt','')).strip() not in ('1','1.0'):continue
  player=(r.get('receiver_player_id') or '').strip();team=(r.get('posteam') or '').strip().upper();week=(r.get('week') or '').strip()
  if not player or not team or not week:continue
  if key in seen:raise SystemExit('Duplicate first-read target event')
  seen.add(key)
  counts[(str(season),week,team,player)]+=1
  team_counts[(str(season),week,team)]+=1
 if not matched or not counts:raise SystemExit('No matched FTN first-read targets; preserving null')
 return counts,team_counts,matched
def main():
 p=argparse.ArgumentParser();p.add_argument('--season',type=int,default=2026);p.add_argument('--output',default='tmp/nfl_wr_ftn_first_reads.csv');a=p.parse_args()
 counts,teams,matched=build(fetch(FTN.format(season=a.season)),fetch(PBP.format(season=a.season),True),a.season)
 out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=['season','week','team','player_id','first_read_targets','team_first_read_targets']);writer.writeheader()
  for (season,week,team,player),n in sorted(counts.items()):
   writer.writerow(dict(season=season,week=week,team=team,player_id=player,first_read_targets=n,team_first_read_targets=teams[(season,week,team)]))
 print('FTN/PBP joined',matched,'plays;',sum(counts.values()),'first or designed read targets')
if __name__=='__main__':main()
