#!/usr/bin/env python3
"""Normalize nflverse PFR snap counts using an explicit, unique PFR->GSIS mapping.
Never equate PFR IDs to GSIS IDs and never match players on names alone.
"""
import argparse,csv,io,pathlib,urllib.request
URL='https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_{season}.csv'
def read_mapping(path):
 if not path:return {}
 with open(path,newline='',encoding='utf-8-sig') as f:
  reader=csv.DictReader(f)
  if not reader.fieldnames:raise SystemExit('Empty player crosswalk')
  pfr=next((x for x in ('pfr_id','pfr_player_id','pfr_id_player') if x in reader.fieldnames),None)
  gsis=next((x for x in ('gsis_id','player_id') if x in reader.fieldnames),None)
  if not pfr or not gsis:raise SystemExit('Crosswalk requires explicit PFR and GSIS columns')
  mapping={};ambiguous=set()
  for r in reader:
   a=(r.get(pfr) or '').strip();b=(r.get(gsis) or '').strip()
   if not a or not b:continue
   if a in mapping and mapping[a]!=b:ambiguous.add(a)
   else:mapping[a]=b
  for a in ambiguous:mapping.pop(a,None)
  return mapping
def normalize(rows,season,mapping):
 if not rows:return []
 names=set(rows[0])
 id_field=next((x for x in ('gsis_id','player_id','pfr_id','pfr_player_id','pfr_id_player') if x in names),None)
 team_field=next((x for x in ('team','recent_team') if x in names),None)
 snap_field=next((x for x in ('offense_snaps','offensive_snaps','off_snaps') if x in names),None)
 if not id_field or not team_field or not snap_field or not {'season','week'}.issubset(names):
  raise SystemExit('Unsupported snap schema: '+','.join(sorted(names)))
 pfr=id_field.startswith('pfr')
 if pfr and not mapping:raise SystemExit('PFR IDs require verified GSIS crosswalk; refusing name-based join')
 output=[];seen=set()
 for row in rows:
  if str(row.get('season'))!=str(season):continue
  raw=(row.get(id_field) or '').strip()
  player_id=mapping.get(raw) if pfr else raw
  team=(row.get(team_field) or '').strip().upper()
  value=(row.get(snap_field) or '').strip()
  if not player_id or not team or not value:continue
  try:
   n=float(value)
   if not (0<=n<=200):continue
  except ValueError:continue
  key=(str(season),str(row['week']),team,player_id)
  if key in seen:raise SystemExit('Duplicate snap key: '+str(key))
  seen.add(key)
  output.append(dict(season=season,week=row['week'],team=team,player_id=player_id,offensive_snaps=value))
 return output
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--season',type=int,default=2026)
 p.add_argument('--output',default='tmp/nfl_wr_snap_counts.csv')
 p.add_argument('--crosswalk',default='data/nfl_wr_verified/pfr_gsis_crosswalk.csv')
 a=p.parse_args()
 req=urllib.request.Request(URL.format(season=a.season),headers={'User-Agent':'KSL-WR-Opportunity/1.0'})
 with urllib.request.urlopen(req,timeout=45) as response:raw=response.read(20000000)
 rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
 mapping=read_mapping(a.crosswalk) if pathlib.Path(a.crosswalk).exists() else {}
 normalized=normalize(rows,a.season,mapping)
 if not normalized:raise SystemExit('No verified GSIS-compatible snap rows; refusing empty output')
 out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=['season','week','team','player_id','offensive_snaps'])
  writer.writeheader();writer.writerows(normalized)
 print('Normalized',len(normalized),'verified snap rows')
if __name__=='__main__':main()
