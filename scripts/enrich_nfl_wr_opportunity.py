#!/usr/bin/env python3
"""Join explicitly licensed, verified supplemental player-game stats into WR feed.

CSV columns: season,week,team,player_id, plus any of:
offensive_snaps,routes_run,team_dropbacks,first_read_targets,
team_first_read_targets,end_zone_targets,team_end_zone_targets.
Only joins exact IDs and game keys. Missing stays null; ambiguous keys fail closed.
Usage: python scripts/enrich_nfl_wr_opportunity.py --input feed/nfl_wr_opportunity.json --supplement data.csv --source 'provider + license' --output feed/nfl_wr_opportunity.json
"""
import argparse,csv,json,math,pathlib
METRICS=('offensive_snaps','routes_run','team_dropbacks','first_read_targets','team_first_read_targets','end_zone_targets','team_end_zone_targets')
def numeric(v):
    if v is None or str(v).strip()=='':return None
    try:
        n=float(v)
        if math.isfinite(n) and n>=0:return n
    except (TypeError,ValueError):pass
    raise ValueError('Invalid nonnegative metric: '+str(v))
def validate_route_metrics(row, incoming, record_key):
    """Reject impossible charting values rather than publishing false route efficiency."""
    def effective(field):
        return incoming.get(field) if incoming.get(field) is not None else row.get(field)
    for field in ('routes_run','team_dropbacks'):
        value=effective(field)
        if value is not None and (not float(value).is_integer() or value < 0):
            raise SystemExit('Invalid route metric count: '+str(record_key)+' '+field)
    routes=effective('routes_run')
    snaps=effective('offensive_snaps')
    if routes is not None and snaps is not None and routes > snaps:
        raise SystemExit('Routes exceed offensive snaps: '+str(record_key))
    dropbacks=effective('team_dropbacks')
    if routes is not None and dropbacks is not None and routes > dropbacks:
        raise SystemExit('Routes exceed team dropbacks: '+str(record_key))
def key(row):
    return (str(row.get('season','')),str(row.get('week','')),str(row.get('team','')).upper(),str(row.get('player_id','')))
def main():
    p=argparse.ArgumentParser()
    for arg in ('input','supplement','source','output'):p.add_argument('--'+arg,required=True)
    a=p.parse_args()
    if not a.source.strip():raise SystemExit('Source attribution required')
    data=json.loads(pathlib.Path(a.input).read_text())
    with open(a.supplement,newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        required={'season','week','team','player_id'}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):raise SystemExit('Missing exact join keys')
        columns=[x for x in METRICS if x in reader.fieldnames]
        if not columns:raise SystemExit('No supported metrics in supplement')
        supplements={}
        for row in reader:
            k=key(row)
            if k in supplements:raise SystemExit('Duplicate supplement key: '+str(k))
            supplements[k]={x:numeric(row.get(x)) for x in columns}
    matched=0;updated=0
    for row in data.get('games',[]):
        k=key(row)
        if k not in supplements:continue
        matched+=1
        validate_route_metrics(row,supplements[k],k)
        provenance=row.setdefault('metric_sources',{})
        for field,value in supplements[k].items():
            if value is None:continue
            existing=row.get(field)
            if existing is not None and abs(float(existing)-value)>0.001:
                raise SystemExit('Conflicting verified metric: '+str(k)+' '+field)
            row[field]=value
            provenance[field]=a.source
            updated+=1
    if not matched or not updated:raise SystemExit('No valid matching supplemental data; refusing empty update')
    pathlib.Path(a.output).write_text(json.dumps(data,separators=(',',':'))+'\n')
    print('Joined',matched,'player-games, updated',updated,'metrics from',a.source)
if __name__=='__main__':main()
