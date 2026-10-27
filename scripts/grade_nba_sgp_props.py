"""Fail-closed NBA SGP ledger grader. Never infer sportsbook/ESPN event identity."""
import json
from pathlib import Path
from datetime import datetime,timezone

LEDGER=Path("feed/nba_prop_pregame_ledger.jsonl")
OUTPUT=Path("feed/nba_prop_pregame_grades.json")
MARKETS={"player_points","player_rebounds","player_assists","player_threes"}
COMPLETED=Path("feed/nba_completed_games.json")

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
    grades=[{"event_id":r.get("event_id"),"espn_event_id":crosswalk.get(r.get("event_id"),{}).get("espn_event_id"),"player":r.get("player"),"market":r.get("market"),"selection":r.get("selection"),"line":r.get("point"),"bookmaker":r.get("bookmaker"),"captured_at":r.get("captured_at"),"status":"UNVERIFIED","reason":assess(r) if r.get("event_id") in crosswalk else "verified game crosswalk unavailable"} for r in rows]
    OUTPUT.write_text(json.dumps({"generated_at":datetime.now(timezone.utc).isoformat(),"records":len(grades),"graded":0,"unverified":len(grades),"matched_games":len(crosswalk),"grades":grades},indent=2)+"\n")
    print("NBA SGP pregame ledger: ",len(grades),"records; 0 graded without verified crosswalk")

if __name__=="__main__":
    main()
