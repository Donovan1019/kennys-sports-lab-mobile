#!/usr/bin/env python3
"""Validate externally supplied NFL player report snapshot without inventing entries."""
import json,sys
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.parse import urlparse

SCHEDULE=Path('feed/americanfootball_nfl.json')

ALLOWED={"nfl.com","www.nfl.com","espn.com","www.espn.com"}
STATUS={"game_designation":{"out","doubtful","questionable"},"official_inactives":{"active","inactive"}}
def parse_time(value):
    if not isinstance(value,str):raise ValueError("timestamp missing")
    t=datetime.fromisoformat(value.replace("Z","+00:00"))
    if t.tzinfo is None:raise ValueError("timezone required")
    return t
def validate(data,now=None,schedule=None):
    now=now or datetime.now(timezone.utc)
    if not isinstance(data,dict) or not isinstance(data.get("reports"),list):raise ValueError("reports array required")
    if not data["reports"]:raise ValueError("No verified reports to publish")
    if schedule is not None:
        fetched_schedule=parse_time(schedule.get('fetched_at'))
        if fetched_schedule>now or now-fetched_schedule>=timedelta(hours=6):raise ValueError('Stale NFL event schedule')
    events={}
    if schedule and isinstance(schedule.get('odds'),list):
        for row in schedule['odds']:
            if isinstance(row,dict) and row.get('event_id') and isinstance(row.get('event'),str):
                old=events.get(row['event_id'])
                if old and (old.get('event')!=row.get('event') or old.get('commence_time')!=row.get('commence_time')):raise ValueError('Conflicting NFL event records')
                events[row['event_id']]=row
    seen=set()
    for report in data["reports"]:
        if not isinstance(report,dict) or report.get("verified") is not True:raise ValueError("Unverified report")
        kind=report.get("report_type")
        if kind not in STATUS:raise ValueError("Invalid report type")
        if not isinstance(report.get("event_id"),str) or not report["event_id"].strip():raise ValueError("Event id required")
        key=(report['event_id'],kind)
        if key in seen:raise ValueError('Duplicate report type for event')
        seen.add(key)
        if schedule is not None:
            event=events.get(report['event_id'])
            if not event:raise ValueError('Unknown event id')
            teams=event['event'].split(' @ ')
            if len(teams)!=2:raise ValueError('Invalid event teams')
            if any(p.get('team') not in teams for p in report.get('players',[]) if isinstance(p,dict)):raise ValueError('Player team mismatch')
            if report['report_type']=='official_inactives' and now < parse_time(event.get('commence_time'))-timedelta(minutes=90):raise ValueError('Premature official inactives')
        parsed=urlparse(str(report.get("source_url","")))
        if parsed.scheme!="https" or parsed.hostname not in ALLOWED or parsed.username or parsed.password:raise ValueError("Untrusted source")
        fetched=parse_time(report.get("fetched_at"))
        if fetched>now or (now-fetched).total_seconds()>=21600:raise ValueError("Stale source")
        players=report.get("players")
        if not isinstance(players,list) or not players:raise ValueError("Empty report")
        seen_players=set()
        for player in players:
            if not isinstance(player,dict) or not all(isinstance(player.get(k),str) and player[k].strip() for k in ("name","team")):raise ValueError("Missing player identity")
            if player.get("status") not in STATUS[kind]:raise ValueError("Wrong status for report type")
            player_key=(player['team'].strip().casefold(),player['name'].strip().casefold())
            if player_key in seen_players:raise ValueError('Duplicate player status')
            seen_players.add(player_key)
    return len(data["reports"])
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: validate_nfl_injury_reports.py PATH")
    schedule=json.loads(SCHEDULE.read_text(encoding='utf-8')) if SCHEDULE.exists() else None
    if schedule is None:raise SystemExit('Cannot validate publication without current NFL event schedule')
    count=validate(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')),schedule=schedule)
    print("Validated",count,"source-backed injury reports")
