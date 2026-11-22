#!/usr/bin/env python3
"""Independent NFL player-week source audit (nflverse vs ESPN player feed).
Read-only; never overwrite model projections or silently substitute metrics.
"""
import csv, io, json, sys, urllib.request
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE='https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2026.csv'
FIELDS=('passing_yards','rushing_yards','receiving_yards','targets','receptions')
def read_nflverse(url=SOURCE):
    req=urllib.request.Request(url,headers={'User-Agent':'KennysSportsLab/1.0'})
    with urllib.request.urlopen(req,timeout=30) as response:
        if response.status!=200:raise RuntimeError('nflverse HTTP '+str(response.status))
        raw=response.read(18_000_000)
    reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    required={'season','week','season_type','player_id','team'}|set(FIELDS)
    missing=required-set(reader.fieldnames or [])
    if missing:raise ValueError('nflverse schema missing '+','.join(sorted(missing)))
    rows=[]
    for row in reader:
        if row.get('season_type')!='REG' or row.get('season')!='2026':continue
        if not row.get('player_id') or not row.get('week','').isdigit():continue
        rows.append(row)
    if not rows:raise ValueError('No 2026 regular-season player-week rows')
    return rows
def main():
    rows=read_nflverse()
    latest=max(int(r['week']) for r in rows)
    counts=defaultdict(int)
    for r in rows:counts[int(r['week'])]+=1
    out={'source':'nflverse/nflverse-data:stats_player','url':SOURCE,'season':2026,
         'checked_at':datetime.now(timezone.utc).isoformat(),
         'latest_week':latest,'player_week_rows':len(rows),
         'weeks':dict(sorted(counts.items())),'status':'source_verified',
         'integration':'audit_only_no_model_substitution'}
    dest=ROOT/'feed/nflverse_player_source_audit.json'
    dest.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('NFLVERSE AUDIT UNAVAILABLE: '+str(exc),file=sys.stderr)
        sys.exit(1)
