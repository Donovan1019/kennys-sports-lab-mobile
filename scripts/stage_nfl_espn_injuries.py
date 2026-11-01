#!/usr/bin/env python3
"""Stage ESPN NFL injury players without asserting game-day status or publishing predictions."""
import json
import urllib.request
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse
from discover_nfl_espn_injuries import URL,MAX_BYTES

DEST=Path('feed/nfl_injury_espn_player_staging.json')
def stage(payload,fetched_at):
    if not isinstance(payload,dict) or not isinstance(payload.get('injuries'),list):
        raise ValueError('ESPN injury groups missing')
    groups=[];seen=set()
    for group in payload['injuries']:
        if not isinstance(group,dict):continue
        team_id=group.get('id');team_name=group.get('displayName');injuries=group.get('injuries')
        if not isinstance(team_id,str) or not team_id.strip() or not isinstance(team_name,str) or not team_name.strip() or not isinstance(injuries,list):continue
        players=[]
        for item in injuries:
            if not isinstance(item,dict) or not isinstance(item.get('athlete'),dict):continue
            athlete=item['athlete'];name=athlete.get('fullName');athlete_id=athlete.get('id')
            if not isinstance(name,str) or not name.strip() or not isinstance(athlete_id,str) or not athlete_id.strip():continue
            key=(team_id,athlete_id)
            if key in seen:continue
            seen.add(key)
            raw_status=item.get('status')
            players.append({'athlete_id':athlete_id,'name':name.strip(),'raw_status':raw_status if isinstance(raw_status,str) else None,'injury_date':item.get('date') if isinstance(item.get('date'),str) else None})
        if players:groups.append({'espn_team_id':team_id,'team_name':team_name,'players':players})
    return {'source_url':URL,'fetched_at':fetched_at,'source_reported_at':payload.get('timestamp') if isinstance(payload.get('timestamp'),str) else None,'status':'STAGED_UNVERIFIED','verified_player_reports':0,'projection_impact':'NOT_APPLIED','teams':groups}

def main():
    req=urllib.request.Request(URL,headers={'User-Agent':'Mozilla/5.0 KennySportsLab/1.0','Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=25) as response:
        parsed=urlparse(response.geturl())
        if parsed.scheme!='https' or parsed.hostname!='site.api.espn.com':raise ValueError('Untrusted redirect')
        if 'json' not in response.headers.get('Content-Type','').lower():raise ValueError('Unexpected content type')
        body=response.read(MAX_BYTES+1)
        if len(body)>MAX_BYTES:raise ValueError('Oversize response')
    data=stage(json.loads(body),datetime.now(timezone.utc).isoformat())
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':data['status'],'teams':len(data['teams']),'players':sum(len(g['players']) for g in data['teams']),'verified_player_reports':0}))
if __name__=='__main__':main()
