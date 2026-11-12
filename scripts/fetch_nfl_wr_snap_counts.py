#!/usr/bin/env python3
"""Fetch public nflverse PFR snap counts; only exact ID joins are accepted.

No name-only joins. Unknown source schema or inaccessible source fails closed.
"""
import argparse,csv,io,pathlib,urllib.request
URL='https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_{season}.csv'
def main():
 p=argparse.ArgumentParser();p.add_argument('--season',type=int,default=2026);p.add_argument('--output',default='tmp/nfl_wr_snap_counts.csv');a=p.parse_args()
 req=urllib.request.Request(URL.format(season=a.season),headers={'User-Agent':'KSL-WR-Opportunity/1.0'})
 with urllib.request.urlopen(req,timeout=45) as response:raw=response.read(20000000)
 rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
 if not rows:raise SystemExit('Snap source empty')
 names=set(rows[0])
 id_field=next((x for x in ('gsis_id','player_id') if x in names),None)
 team_field=next((x for x in ('team','recent_team') if x in names),None)
 snap_field=next((x for x in ('offense_snaps','offensive_snaps') if x in names),None)
 if not id_field or not team_field or not snap_field or not {'season','week'}.issubset(names):
  raise SystemExit('No confirmed GSIS-compatible ID or snap columns: refusing unsafe mapping')
 out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=['season','week','team','player_id','offensive_snaps']);writer.writeheader()
  for row in rows:
   if str(row.get('season'))!=str(a.season):continue
   writer.writerow({'season':row['season'],'week':row['week'],'team':row[team_field],'player_id':row[id_field],'offensive_snaps':row[snap_field]})
 print('Normalized verified snap rows:',out)
if __name__=='__main__':main()
