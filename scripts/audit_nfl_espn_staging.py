#!/usr/bin/env python3
"""Audit staged ESPN injury records; never promote raw feed statuses to official designations."""
import json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

STAGING=Path('feed/nfl_injury_espn_player_staging.json')
DEST=Path('feed/nfl_injury_espn_quality_audit.json')

def audit(data):
    if not isinstance(data,dict) or data.get('status')!='STAGED_UNVERIFIED' or not isinstance(data.get('teams'),list):
        raise ValueError('Expected unverified ESPN staging file')
    if data.get('verified_player_reports')!=0:raise ValueError('Staging unexpectedly claims verification')
    statuses=Counter();dated=0;missing=0;duplicates=0;seen=set();players=0
    for team in data['teams']:
        if not isinstance(team,dict) or not isinstance(team.get('players'),list):raise ValueError('Malformed team group')
        team_id=team.get('espn_team_id')
        if not isinstance(team_id,str) or not team_id:raise ValueError('Missing team identity')
        for p in team['players']:
            if not isinstance(p,dict):raise ValueError('Malformed player')
            name=p.get('name')
            if not isinstance(name,str) or not name.strip():missing+=1;continue
            key=(team_id,name.strip().casefold())
            if key in seen:duplicates+=1
            seen.add(key);players+=1
            status=p.get('raw_status')
            statuses[status.strip() if isinstance(status,str) and status.strip() else 'MISSING']+=1
            if isinstance(p.get('injury_date'),str) and p['injury_date'].strip():dated+=1
    if players==0:raise ValueError('No staged player identities')
    return {'status':'AUDITED_UNVERIFIED','source_url':data.get('source_url'),'fetched_at':data.get('fetched_at'),'teams':len(data['teams']),'players':players,'missing_names':missing,'duplicate_names':duplicates,'dated_records':dated,'raw_status_counts':dict(sorted(statuses.items())),'verified_player_reports':0,'publication_allowed':False,'projection_impact':'NOT_APPLIED'}

def main():
    result=audit(json.loads(STAGING.read_text(encoding='utf-8')))
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))
if __name__=='__main__':main()
