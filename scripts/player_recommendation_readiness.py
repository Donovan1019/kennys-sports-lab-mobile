"""Audit player betting recommendation readiness without inventing selections or consuming paid APIs."""
import json
import math
from datetime import datetime, timezone
from pathlib import Path

SPORTS={"NFL":"americanfootball_nfl","NBA":"basketball_nba","NHL":"icehockey_nhl"}
REQUIRED=("bet_eligible","status","verified_market","simulation_verified","lineup_verified","market_fresh","is_player_prop","player","market","selection","point","hit_probability","market_odds_american","expected_value","verified_at")
def audit(feed):
    missing=[]
    for field in REQUIRED:
        if field not in feed:missing.append(field)
    if feed.get("bet_eligible") is not True:missing.append("bet_eligible_true")
    if feed.get("status")!="verified":missing.append("status_verified")
    for field in ("verified_market","simulation_verified","lineup_verified","market_fresh","is_player_prop"):
        if feed.get(field) is not True:missing.append(field+"_true")
    for field in ("player","market","selection"):
        if not isinstance(feed.get(field),str) or not feed[field].strip():missing.append(field+"_value")
    for field in ("point","hit_probability","market_odds_american","expected_value"):
        if isinstance(feed.get(field),bool) or not isinstance(feed.get(field),(float,int)):missing.append(field+"_numeric")
    return sorted(set(missing))
def inspect_nfl_quote_archive(path, event_feed_path=Path("feed/americanfootball_nfl.json"), now=None):
    """Check free, already archived quotes; never infer player team from event name."""
    if not path.exists():
        return {"status":"unavailable","quotes":0,"fresh_quotes":0,"event_count":0,"unverified_player_team_assignments":0}
    data=json.loads(path.read_text())
    rows=data.get("odds",[])
    now=now or datetime.now(timezone.utc)
    event_data=json.loads(event_feed_path.read_text()) if event_feed_path.exists() else {}
    event_rows=event_data.get("odds",[])
    known_events={}
    for event_row in event_rows:
        if not isinstance(event_row,dict):continue
        eid=event_row.get("event_id")
        identity=(event_row.get("event"),event_row.get("commence_time"))
        if eid and all(identity):known_events.setdefault(eid,set()).add(identity)
    matched_event_rows=0
    unmatched_event_rows=0
    event_conflict_rows=0
    future_dated_rows=0
    valid=0
    events=set()
    invalid=0
    for row in rows:
        try:
            when=datetime.fromisoformat(row["updated_at"].replace("Z","+00:00"))
            start=datetime.fromisoformat(row["commence_time"].replace("Z","+00:00"))
            price=row["price"]
            if not isinstance(price,(int,float)) or isinstance(price,bool) or not math.isfinite(price) or price==0:
                invalid+=1
                continue
            if not row.get("player") or not row.get("bookmaker") or not row.get("market") or not row.get("event_id"):
                invalid+=1
                continue
            events.add(row["event_id"])
            identity=(row.get("event"),row.get("commence_time"))
            candidates=known_events.get(row["event_id"],set())
            if not candidates:unmatched_event_rows+=1
            elif identity not in candidates or len(candidates)!=1:event_conflict_rows+=1
            else:matched_event_rows+=1
            if when>now:future_dated_rows+=1
            if 0<=(now-when).total_seconds()<=3600 and start>now:
                valid+=1
        except (KeyError,ValueError,TypeError,AttributeError):
            invalid+=1
    return {"status":"archived_reference_only_not_bet_eligible","quotes":len(rows),
            "fresh_quotes":valid,"event_count":len(events),"invalid_quote_rows":invalid,
            "unverified_player_team_assignments":len(rows),
            "matched_archived_event_rows":matched_event_rows,
            "unmatched_archived_event_rows":unmatched_event_rows,
            "conflicting_archived_event_rows":event_conflict_rows,
            "future_dated_quote_rows":future_dated_rows,
            "current_roster_source_connected":False,
            "verified_player_team_assignments":0,
            "warning":"No independent player-team roster matching, lineup confirmation, player projections, or simulations. Do not promote quotes to betting picks."}

def main():
    now=datetime.now(timezone.utc).isoformat()
    output={"generated_at":now,"status":"research_only_until_verified","sports":{}}
    for sport,slug in SPORTS.items():
        path=Path("feed")/(slug+"_pregame_research.json")
        data=json.loads(path.read_text()) if path.exists() else {}
        events=data.get("events",[])
        counts={}
        for e in events:
            for field in audit(e):
                counts[field]=counts.get(field,0)+1
        output["sports"][sport]={"researched_events":len(events),"fully_verified_player_recommendations":0,"missing_field_counts":counts,"note":"Event-level pregame research does not establish verified player-specific props; no betting selections issued."}
    output["source_integrity"]={"NFL_archived_player_props":inspect_nfl_quote_archive(Path("feed/nfl_props.json"))}
    path=Path("feed/player_recommendation_readiness.json")
    path.write_text(json.dumps(output,indent=2)+"\n")
    print("Player recommendation audit: "+", ".join(f"{k} {v['researched_events']} events, 0 verified props" for k,v in output["sports"].items()))
if __name__=="__main__":main()
