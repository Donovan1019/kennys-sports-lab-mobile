"""Fail-closed NBA SGP ledger grader. Never infer sportsbook/ESPN event identity."""
import json
from pathlib import Path
from datetime import datetime,timezone

LEDGER=Path("feed/nba_prop_pregame_ledger.jsonl")
OUTPUT=Path("feed/nba_prop_pregame_grades.json")
MARKETS={"player_points","player_rebounds","player_assists","player_threes"}
COMPLETED=Path("feed/nba_completed_games.json")
PLAYER_STATS=Path("feed/nba_player_stats.json")
SGP_LEDGER=Path("feed/nba_sgp_pregame_ledger.jsonl")
SGP_GRADES=Path("feed/nba_sgp_pregame_grades.json")
METRICS={"player_points":"Points","player_rebounds":"Rebounds","player_assists":"Assists","player_threes":"Threes"}

def timestamp(value):
    try:
        parsed=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except (ValueError,TypeError,AttributeError):
        return None

def normalize_team(value):
    import re
    return re.sub(r"[^a-z0-9]+","",str(value or "").casefold())

def build_crosswalk(rows):
    """Only exact ordered teams and UTC tipoff within 15 min; no guessing."""
    try:
        games=json.loads(COMPLETED.read_text()).get("games",[])
    except (OSError,ValueError,AttributeError):
        games=[]
    crosswalk={}
    for row in rows:
        event=row.get("event_id")
        if not event or event in crosswalk:
            continue
        start=timestamp(row.get("commence_time"))
        label=str(row.get("event") or "")
        if not start or " @ " not in label:
            continue
        away,home=label.split(" @ ",1)
        candidates=[]
        for game in games:
            date=timestamp(game.get("date"))
            if not date or abs((date-start).total_seconds())>900:
                continue
            if normalize_team(game.get("away"))!=normalize_team(away) or normalize_team(game.get("home"))!=normalize_team(home):
                continue
            candidates.append(game)
        if len(candidates)==1 and candidates[0].get("event_id"):
            crosswalk[event]={"espn_event_id":str(candidates[0]["event_id"]),"match":"exact ordered teams and start within 15 minutes"}
    return crosswalk

def assess(row):
    start=timestamp(row.get("commence_time"))
    captured=timestamp(row.get("captured_at"))
    quoted=timestamp(row.get("updated_at"))
    if not all((start,captured,quoted)):
        return "invalid or missing timestamp"
    if captured>=start or quoted>=start:
        return "quote or snapshot not verified before tipoff"
    if row.get("market") not in MARKETS:
        return "unsupported market"
    if row.get("selection") not in ("Over","Under"):
        return "unsupported side"
    try:
        if float(row["point"])<0:
            return "invalid threshold"
    except (KeyError,TypeError,ValueError):
        return "invalid threshold"
    if not row.get("player") or not row.get("event_id"):
        return "missing player or event"
    return "verified sportsbook-to-completed-game player crosswalk unavailable"

def verified_player_outcomes():
    try:
        data=json.loads(PLAYER_STATS.read_text())
        if data.get("source")!="espn-public-boxscore" or data.get("sport")!="nba":
            return {}
        players=data.get("players",[])
    except (OSError,ValueError,AttributeError):
        return {}
    lookup={}
    for player in players:
        name=str(player.get("name") or "").strip().casefold()
        ident=str(player.get("id") or "")
        if not name or not ident:
            continue
        for game in player.get("games",[]):
            event=str(game.get("game_id") or "")
            if event and isinstance(game.get("values"),dict):
                lookup.setdefault((event,name),[]).append((ident,game["values"]))
    return lookup

def verified_grade(row,event_id,lookup):
    reason=assess(row)
    if reason!="verified sportsbook-to-completed-game player crosswalk unavailable":
        return "UNVERIFIED",reason
    matches=lookup.get((event_id,str(row.get("player") or "").strip().casefold()),[])
    if len(matches)!=1:
        return "UNVERIFIED","unique completed-game player boxscore unavailable"
    metric=METRICS.get(row.get("market"))
    value=matches[0][1].get(metric)
    if not isinstance(value,(int,float)) or isinstance(value,bool):
        return "UNVERIFIED","verified boxscore metric unavailable"
    line=float(row["point"])
    if value==line:
        return "PUSH","verified exact-line push"
    won=(value>line) if row["selection"]=="Over" else (value<line)
    return ("WIN" if won else "LOSS"),"verified pregame quote and ESPN completed-game player boxscore"

def grade_saved_sgps(rows,crosswalk,lookup):
    """Grade only explicitly captured combinations; never synthesize SGPs."""
    records=[]
    if SGP_LEDGER.exists():
        for line in SGP_LEDGER.read_text().splitlines():
            try:
                item=json.loads(line)
                if isinstance(item,dict):
                    records.append(item)
            except json.JSONDecodeError:
                continue
    output=[]
    for item in records:
        legs=item.get("legs")
        captured=timestamp(item.get("captured_at"))
        event=item.get("event_id")
        match=crosswalk.get(event)
        status="UNVERIFIED"
        reason="verified pregame combination unavailable"
        if not isinstance(legs,list) or not 2<=len(legs)<=12:
            reason="invalid SGP leg count"
        elif not captured or not match:
            reason="missing capture time or verified game crosswalk"
        elif any(not isinstance(leg,dict) or leg.get("event_id")!=event or timestamp(leg.get("captured_at"))!=captured for leg in legs):
            reason="legs not tied to the same captured game snapshot"
        else:
            outcomes=[verified_grade(leg,match["espn_event_id"],lookup) for leg in legs]
            states=[x[0] for x in outcomes]
            if "UNVERIFIED" in states:
                reason="at least one leg unverified"
            elif "LOSS" in states:
                status,reason="LOSS","verified losing leg"
            elif "PUSH" in states:
                status,reason="UNVERIFIED","SGP push/void settlement requires sportsbook-specific rules"
            elif all(x=="WIN" for x in states):
                status,reason="WIN","all legs verified winners; settlement subject to sportsbook rules"
        output.append({"sgp_id":item.get("sgp_id"),"event_id":event,"leg_count":len(legs) if isinstance(legs,list) else None,"status":status,"reason":reason})
    SGP_GRADES.write_text(json.dumps({"generated_at":datetime.now(timezone.utc).isoformat(),"records":len(output),"graded":sum(x["status"] in ("WIN","LOSS") for x in output),"unverified":sum(x["status"]=="UNVERIFIED" for x in output),"grades":output},indent=2)+"\\n")
    return output

def main():
    rows=[]
    if LEDGER.exists():
        for line in LEDGER.read_text().splitlines():
            try:
                row=json.loads(line)
                if isinstance(row,dict):
                    rows.append(row)
            except json.JSONDecodeError:
                continue
    crosswalk=build_crosswalk(rows)
    lookup=verified_player_outcomes()
    grades=[]
    for row in rows:
        matched=crosswalk.get(row.get("event_id"))
        status,reason=verified_grade(row,matched["espn_event_id"],lookup) if matched else ("UNVERIFIED","verified game crosswalk unavailable")
        grades.append({"event_id":row.get("event_id"),"espn_event_id":matched["espn_event_id"] if matched else None,"player":row.get("player"),"market":row.get("market"),"selection":row.get("selection"),"line":row.get("point"),"bookmaker":row.get("bookmaker"),"captured_at":row.get("captured_at"),"status":status,"reason":reason})
    sgps=grade_saved_sgps(rows,crosswalk,lookup)
    OUTPUT.write_text(json.dumps({"generated_at":datetime.now(timezone.utc).isoformat(),"records":len(grades),"graded":sum(x["status"] in ("WIN","LOSS","PUSH") for x in grades),"unverified":sum(x["status"]=="UNVERIFIED" for x in grades),"matched_games":len(crosswalk),"grades":grades},indent=2)+"\n")
    print("NBA SGP pregame ledger:",len(grades),"records; verified graded:",sum(x["status"] in ("WIN","LOSS","PUSH") for x in grades))

if __name__=="__main__":
    main()
