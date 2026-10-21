"""Fail-closed market snapshot integrity audit; no bet recommendations."""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

def parse_time(value):
    try:
        d=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        return d if d.tzinfo else None
    except (ValueError,TypeError):
        return None

def audit(feed,now=None):
    now=now or datetime.now(timezone.utc)
    rows=feed.get("odds",[])
    reasons=Counter()
    valid=[]
    for r in rows:
        start=parse_time(r.get("commence_time"))
        updated=parse_time(r.get("updated_at"))
        if start is None or updated is None:
            reasons["missing_or_invalid_timestamps"]+=1
        elif start<=now:
            reasons["event_already_started"]+=1
        elif updated>now:
            reasons["future_dated_price"]+=1
        elif (now-updated).total_seconds()>900:
            reasons["stale_price_over_15m"]+=1
        elif not r.get("bookmaker") or not r.get("event_id") or not r.get("selection"):
            reasons["missing_market_identity"]+=1
        elif not isinstance(r.get("price"),(int,float)) or -100<r["price"]<100:
            reasons["invalid_price"]+=1
        else:
            valid.append(r)
    events=len({r["event_id"] for r in valid})
    return {"status":"research_only","generated_at":now.isoformat(),"sport":feed.get("sport"),"total_rows":len(rows),"eligible_pregame_rows":len(valid),"eligible_events":events,"excluded_by_reason":dict(reasons),"betting_ready":False,"notes":["Snapshot is not a historical closing-line database","No wager is approved without verified lineup, model calibration, market settlement and risk checks","Price freshness threshold is 15 minutes; in-play prices are excluded"]}

def main():
    for sport in ("basketball_nba","icehockey_nhl"):
        path=Path(f"feed/{sport}.json")
        if not path.exists():continue
        report=audit(json.loads(path.read_text()))
        out=Path(f"feed/{sport}_odds_integrity.json")
        out.write_text(json.dumps(report,indent=2)+"\n")
        print(sport,json.dumps(report))
if __name__=="__main__":main()
