#!/usr/bin/env python3
"""Discover ESPN's public NFL injury JSON shape without publishing unverified player statuses."""
import json
import urllib.request
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse

URL='https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries'
DEST=Path('feed/nfl_injury_espn_discovery.json')
MAX_BYTES=12_000_000

def inspect_payload(data):
    if not isinstance(data,dict):raise ValueError('Expected JSON object')
    keys=sorted(data.keys())
    candidates={}
    for key,value in data.items():
        if isinstance(value,list):
            candidates[key]={'count':len(value),'first_item_keys':sorted(value[0].keys()) if value and isinstance(value[0],dict) else []}
    return {'top_level_keys':keys,'array_shapes':candidates,'injury_nested_shapes':inspect_nested_injuries(data)}

def inspect_nested_injuries(data):
    rows=data.get('injuries')
    if not isinstance(rows,list):return {'status':'UNAVAILABLE'}
    teams=[]
    for row in rows[:32]:
        if not isinstance(row,dict):continue
        injuries=row.get('injuries')
        if not isinstance(row.get('id'),str) or not isinstance(row.get('displayName'),str) or not isinstance(injuries,list):continue
        first=next((p for p in injuries if isinstance(p,dict)),None)
        teams.append({'team_keys':sorted(row.keys()),'injury_count':len(injuries),'injury_keys':sorted(first.keys()) if first else [],'athlete_keys':sorted(first['athlete'].keys()) if first and isinstance(first.get('athlete'),dict) else []})
    return {'status':'SCHEMA_ONLY','teams_with_arrays':len(teams),'sample_shapes':teams[:3],'all_injury_keys':sorted({key for row in rows if isinstance(row,dict) for injury in (row.get('injuries') if isinstance(row.get('injuries'),list) else []) if isinstance(injury,dict) for key in injury.keys()}),'all_team_keys':sorted({key for row in rows if isinstance(row,dict) for key in row.keys()}),'all_athlete_keys':sorted({key for row in rows if isinstance(row,dict) for injury in (row.get('injuries') if isinstance(row.get('injuries'),list) else []) if isinstance(injury,dict) and isinstance(injury.get('athlete'),dict) for key in injury['athlete'].keys()})}

def main():
    record={'checked_at':datetime.now(timezone.utc).isoformat(),'source_url':URL,'status':'UNAVAILABLE','verified_player_reports':0,'player_ingestion_enabled':False}
    try:
        req=urllib.request.Request(URL,headers={'User-Agent':'Mozilla/5.0 KennySportsLab/1.0','Accept':'application/json'})
        with urllib.request.urlopen(req,timeout=25) as response:
            final=urlparse(response.geturl())
            if final.scheme!='https' or final.hostname!='site.api.espn.com':raise ValueError('Unexpected redirect')
            if 'json' not in response.headers.get('Content-Type','').lower():raise ValueError('Unexpected content type')
            payload=response.read(MAX_BYTES+1)
            if len(payload)>MAX_BYTES:raise ValueError('Response too large')
            record.update(inspect_payload(json.loads(payload)))
            record['status']='SCHEMA_DISCOVERED_NOT_VALIDATED'
            record['final_source_url']=response.geturl()
    except Exception as error:
        record['reason']=type(error).__name__
        record['failure_detail']=str(error)[:180]
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':record['status'],'reason':record.get('reason'),'top_level_keys':record.get('top_level_keys'),'nested':record.get('injury_nested_shapes',{}).get('status')}))
if __name__=='__main__':main()
