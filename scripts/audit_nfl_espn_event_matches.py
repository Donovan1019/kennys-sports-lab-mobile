#!/usr/bin/env python3
"""Conservative ESPN team-to-schedule audit; no unverified injury report publication."""
import json
from datetime import datetime,timezone,timedelta
from pathlib import Path

STAGING=Path('feed/nfl_injury_espn_player_staging.json')
SCHEDULE=Path('feed/americanfootball_nfl.json')
DEST=Path('feed/nfl_injury_espn_event_match_audit.json')

def parse_time(value):
    if not isinstance(value,str):raise ValueError('Missing timestamp')
    dt=datetime.fromisoformat(value.replace('Z','+00:00'))
    if dt.tzinfo is None:raise ValueError('Timezone required')
    return dt

def normalize(name):
    return ' '.join(name.casefold().replace('.','').split()) if isinstance(name,str) else ''

def match(staging,schedule,now=None):
    now=now or datetime.now(timezone.utc)
    if not isinstance(staging,dict) or staging.get('status')!='STAGED_UNVERIFIED' or staging.get('verified_player_reports')!=0:raise ValueError('Unverified staging required')
    if not isinstance(schedule,dict) or not isinstance(schedule.get('odds'),list):raise ValueError('NFL schedule missing')
    for item in (staging,schedule):
        timestamp=parse_time(item.get('fetched_at'))
        if timestamp>now+timedelta(minutes=5) or now-timestamp>=timedelta(hours=6):raise ValueError('Stale or future source')
    events={}
    window_start=now-timedelta(hours=4)
    window_end=now+timedelta(days=7)
    for row in schedule['odds']:
        if not isinstance(row,dict) or not isinstance(row.get('event_id'),str) or not isinstance(row.get('event'),str):continue
        parts=row['event'].split(' @ ')
        if len(parts)!=2:continue
        key=row['event_id']
        kickoff=parse_time(row.get('commence_time'))
        if key in events and events[key]!=(tuple(parts),kickoff):raise ValueError('Conflicting schedule event')
        events[key]=(tuple(parts),kickoff)
    if not events:raise ValueError('No NFL events')
    eligible={event_id:teams for event_id,(teams,kickoff) in events.items() if window_start<=kickoff<=window_end}
    teams=staging.get('teams')
    if not isinstance(teams,list) or not teams:raise ValueError('No staged teams')
    output=[];matched=0;ambiguous=0
    for team in teams:
        if not isinstance(team,dict) or not isinstance(team.get('team_name'),str):continue
        name=team['team_name']
        candidates=[event_id for event_id,pair in eligible.items() if normalize(name) in (normalize(pair[0]),normalize(pair[1]))]
        if len(candidates)==1:matched+=1;status='EXACT_NAME_MATCH_UNVERIFIED'
        elif candidates:ambiguous+=1;status='AMBIGUOUS'
        else:status='UNMATCHED'
        output.append({'espn_team_id':team.get('espn_team_id'),'team_name':name,'match_status':status,'candidate_event_ids':sorted(candidates),'staged_players':len(team.get('players',[])) if isinstance(team.get('players'),list) else 0})
    return {'status':'EVENT_MATCH_AUDIT_ONLY','staged_team_count':len(output),'matched_teams':matched,'ambiguous_teams':ambiguous,'unmatched_teams':len(output)-matched-ambiguous,'schedule_event_count':len(events),'eligible_event_count':len(eligible),'team_matches':output,'verified_player_reports':0,'publication_allowed':False,'projection_impact':'NOT_APPLIED'}

def main():
    staging=json.loads(STAGING.read_text(encoding='utf-8'))
    schedule=json.loads(SCHEDULE.read_text(encoding='utf-8'))
    try:
        result=match(staging,schedule)
    except ValueError as error:
        if str(error)!='Stale or future source':raise
        result={'status':'BLOCKED_STALE_SOURCE','reason':'Stale or future source','staged_team_count':len(staging.get('teams',[])),'matched_teams':0,'ambiguous_teams':0,'unmatched_teams':len(staging.get('teams',[])),'schedule_event_count':0,'team_matches':[],'verified_player_reports':0,'publication_allowed':False,'projection_impact':'NOT_APPLIED'}
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='team_matches'}))
if __name__=='__main__':main()
