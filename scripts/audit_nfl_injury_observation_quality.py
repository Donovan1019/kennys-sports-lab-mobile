#!/usr/bin/env python3
"""Offline ESPN injury observation quality audit. No roster or game-day verification."""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

def dt(value):
    try:
        d=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (ValueError,TypeError,OverflowError):return None

def audit(payload, now=None):
    now=now or datetime.now(timezone.utc)
    checked=dt(payload.get("checked_at"))
    rows=payload.get("injuries",[])
    if not isinstance(rows,list):raise ValueError("Invalid injury observations")
    ages=Counter()
    status=Counter()
    teams=set()
    unique=set()
    ids=set()
    conflicts=set()
    seen={}
    for row in rows:
        if not isinstance(row,dict):raise ValueError("Malformed injury row")
        reported=dt(row.get("reported_at"))
        age=(now-reported).total_seconds()/3600 if reported else None
        bucket=("INVALID_TIMESTAMP" if age is None or age<0 else
                "LAST_6_HOURS" if age<=6 else
                "LAST_24_HOURS" if age<=24 else
                "LAST_7_DAYS" if age<=168 else "OLDER_THAN_7_DAYS")
        ages[bucket]+=1
        team=str(row.get("team_id") or row.get("team") or "").strip()
        name=str(row.get("player") or "").strip().casefold()
        if team:teams.add(team)
        if team and name:
            key=(team,name)
            unique.add(key)
            old=seen.setdefault(key,set())
            old.add(str(row.get("status") or "").casefold())
            if len(old)>1:conflicts.add(key)
        if row.get("espn_athlete_id"):ids.add(str(row["espn_athlete_id"]))
        status[str(row.get("status") or "UNKNOWN").strip()]+=1
    freshness=(now-checked).total_seconds()/3600 if checked else None
    return {"generated_at":now.isoformat(),"status":"RESEARCH_ONLY","betting_eligible":False,
            "game_day_availability_verified":False,"identity_crosswalk_verified":False,
            "feed_age_hours":round(freshness,2) if freshness is not None else None,
            "feed_fresh":freshness is not None and 0<=freshness<=6,
            "observations":len(rows),"unique_name_team_pairs":len(unique),
            "teams_observed":len(teams),"source_native_espn_ids":len(ids),
            "conflicting_name_team_statuses":len(conflicts),
            "report_age_buckets":dict(sorted(ages.items())),
            "source_statuses_unverified":dict(sorted(status.items())),
            "blockers":["ESPN_INJURY_STATUS_NOT_CONFIRMED_GAME_DAY","NO_VERIFIED_PLAYER_CROSSWALK"]}

def main():
    root=Path(__file__).resolve().parent.parent/"feed"
    data=json.loads((root/"nfl_injury_observations.json").read_text())
    report=audit(data)
    (root/"nfl_injury_observation_quality.json").write_text(json.dumps(report,indent=2)+"\n")
    print("NFL injury observation quality",json.dumps({k:v for k,v in report.items() if k!="source_statuses_unverified"}))
if __name__=="__main__":main()
