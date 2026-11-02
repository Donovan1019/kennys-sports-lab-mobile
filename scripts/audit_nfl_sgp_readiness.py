#!/usr/bin/env python3
"""Summarize real NFL SGP evidence without promoting research-only results."""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
ROOT=Path(__file__).resolve().parents[1]
def load(path):
    try:
        value=json.loads((ROOT/path).read_text(encoding="utf-8"))
        return value if isinstance(value,dict) else {}
    except (OSError,ValueError):
        return {}
def audit():
    stats=load("feed/nfl_player_stats.json")
    walk=load("feed/nfl_sgp_walkforward_accuracy.json")
    readiness=load("feed/player_recommendation_readiness.json")
    live=load("feed/nfl_props.json")
    now=datetime.now(timezone.utc)
    def parse_time(value):
        try:
            dt=datetime.fromisoformat(value.replace("Z","+00:00"))
            return dt if dt.tzinfo else None
        except (ValueError,TypeError,AttributeError):return None
    fresh=[]
    for q in live.get("odds",[]):
        if not isinstance(q,dict) or q.get("bookmaker") not in ("draftkings","fanduel"):continue
        updated=parse_time(q.get("updated_at"))
        kickoff=parse_time(q.get("commence_time"))
        if updated and kickoff and timedelta(0)<=now-updated<=timedelta(minutes=30) and kickoff>now:fresh.append(q)
    pairs={}
    for q in fresh:
        if q.get("selection") not in ("Over","Under") or not isinstance(q.get("point"),(int,float)):continue
        key=(q.get("event_id"),q.get("bookmaker"),q.get("player"),q.get("market"),q.get("point"))
        pairs.setdefault(key,set()).add(q["selection"])
    paired_count=sum({"Over","Under"}<=sides for sides in pairs.values())
    players=stats.get("players",[])
    if not isinstance(players,list):players=[]
    logs=[g for p in players if isinstance(p,dict) and isinstance(p.get("games"),list) for g in p["games"] if isinstance(g,dict)]
    ids=sum(bool(g.get("game_id") or g.get("event_id")) for g in logs)
    duplicate_ids=len(logs)-len({(p.get("player_id") or p.get("name"),g.get("game_id") or g.get("event_id")) for p in players if isinstance(p,dict) and isinstance(p.get("games"),list) for g in p["games"] if isinstance(g,dict) and (g.get("game_id") or g.get("event_id"))}) if logs and ids==len(logs) else None
    markets=walk.get("frozen_forward_holdout",{}).get("markets",{})
    if not isinstance(markets,dict):markets={}
    market_status={name:{"status":entry.get("status","UNKNOWN"),"eligible_for_live_use":entry.get("eligible_for_live_use") is True} for name,entry in markets.items() if isinstance(entry,dict)}
    nfl=readiness.get("sports",{}).get("NFL",{})
    quotes=readiness.get("source_integrity",{}).get("NFL_archived_player_props",{})
    checks={
        "player_game_logs_present":bool(logs),
        "complete_game_identity":bool(logs) and ids==len(logs),
        "unique_player_game_identity":duplicate_ids==0,
        "all_reported_markets_live_eligible":bool(market_status) and all(x["eligible_for_live_use"] for x in market_status.values()),
        "verified_player_recommendations_present":nfl.get("fully_verified_player_recommendations",0)>0,
        "independent_roster_verification":quotes.get("current_roster_source_connected") is True and quotes.get("verified_player_team_assignments",0)>0,
        "fresh_bookmaker_quotes_present":len(fresh)>0,
        "fresh_same_book_two_way_lines_present":paired_count>0,
        "validated_joint_model_and_ev":False
    }
    return {"status":"BLOCKED" if not all(checks.values()) else "REVIEW_REQUIRED",
            "betting_eligible":False,"checks":checks,"player_game_logs":len(logs),
            "logs_with_game_identity":ids,"duplicate_player_game_ids":duplicate_ids,"market_calibration":market_status,
            "verified_nfl_recommendations":nfl.get("fully_verified_player_recommendations",0),
            "fresh_quote_count":len(fresh),
            "fresh_two_way_pairs":paired_count,
            "quote_freshness_window_minutes":30,
            "reason":"Evidence and independent joint/EV validation required before promotion"}
if __name__=="__main__":
    print(json.dumps(audit(),indent=2,sort_keys=True))
