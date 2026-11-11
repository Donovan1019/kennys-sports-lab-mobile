#!/usr/bin/env python3
"""Credit-aware schedule planner for four-sport market snapshots.

Read-only: never calls an API or consumes credits. Ensures NBA/NHL/NFL/NCAAB
are each considered; stale and absent snapshots are flagged explicitly.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from scripts.build_market_edges import timestamp

SPORTS={"NBA":"basketball_nba","NHL":"icehockey_nhl","NFL":"americanfootball_nfl","NCAAB":"basketball_ncaab"}
REQUIRED=("h2h","spreads","totals")
def audit(root=Path("."),now=None):
    now=now or datetime.now(timezone.utc)
    report={}
    for sport,slug in SPORTS.items():
        path=root/"feed"/(slug+".json")
        try:
            obj=json.loads(path.read_text())
        except (OSError,ValueError,TypeError):
            report[sport]={"status":"MISSING","age_minutes":None,"missing_markets":list(REQUIRED)}
            continue
        if not isinstance(obj,dict):
            report[sport]={"status":"UNVERIFIED","age_minutes":None,"missing_markets":list(REQUIRED),"events_with_quotes":0}
            continue
        odds=obj.get("odds")
        if not isinstance(odds,list):
            odds=[]
        at=timestamp(obj.get("fetched_at"))
        age=(now-at).total_seconds()/60 if at else None
        markets={r.get("market") for r in odds if isinstance(r,dict)}
        missing=sorted(set(REQUIRED)-markets)
        if obj.get("status")!="ok" or obj.get("sport")!=slug or age is None or age<0:
            status="UNVERIFIED"
        elif age>15:
            status="STALE"
        elif missing:
            status="PARTIAL"
        else:
            status="COMPLETE"
        report[sport]={"status":status,"age_minutes":round(age,1) if age is not None else None,"missing_markets":missing,"events_with_quotes":len({r.get("event_id") for r in obj.get("odds",[]) if isinstance(r,dict) and r.get("event_id")})}
    return {"generated_at":now.isoformat(),"status":"COMPLETE" if all(v["status"]=="COMPLETE" for v in report.values()) else "UNAVAILABLE","sports":report,"note":"Read-only coverage audit; no additional Odds API requests or credits used"}
if __name__=="__main__":
    output=Path("data/four_sport_odds_coverage.json")
    output.parent.mkdir(parents=True,exist_ok=True)
    result=audit()
    output.write_text(json.dumps(result,indent=2)+"\n")
    print(result["status"],{k:v["status"] for k,v in result["sports"].items()})
