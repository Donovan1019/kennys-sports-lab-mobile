#!/usr/bin/env python3
"""Summarize DK/FD UFC research feed readiness without manufacturing quotes."""
import argparse
import datetime as dt
import json
from pathlib import Path

def _time(value):
    x=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    if x.utcoffset() is None:
        raise ValueError("UTC offset required")
    return x

def summarize(report, now_utc, max_age_minutes=15):
    now=_time(now_utc)
    providers={}
    for key in ("draftkings","fanduel"):
        feed=report.get("providers",{}).get(key,{})
        state=feed.get("status","MISSING_FEED")
        age=None
        if state=="IMPORTED":
            try:
                stamp=_time(feed["captured_at_utc"])
                age=(now-stamp).total_seconds()/60
                if age<0: state="FUTURE_TIMESTAMP"
                elif age>max_age_minutes: state="STALE_FEED"
                elif not feed.get("markets"): state="EMPTY_FEED"
                else: state="RESEARCH_ONLY"
            except (ValueError,TypeError,KeyError,AttributeError):
                state="INVALID_TIMESTAMP"
        providers[key]={"status":state,"quote_age_minutes":round(age,2) if age is not None else None,
                        "market_count":len(feed.get("markets",[]))}
    counts={}
    for row in report.get("comparisons",[]):
        status=row.get("status","UNKNOWN")
        counts[status]=counts.get(status,0)+1
    ready=all(x["status"]=="RESEARCH_ONLY" for x in providers.values())
    return {"schema":1,"sport":"UFC","checked_at_utc":now_utc,
            "providers":providers,"comparison_status_counts":counts,
            "comparison_ready_for_research":ready,
            "bet_eligible":False,"live_connected":False,
            "blockers":["No authenticated live sportsbook feed",
                        "Independent fighter verification and prospective calibration required"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--now-utc",required=True)
    args=p.parse_args()
    report=summarize(json.loads(Path(args.input).read_text()),args.now_utc)
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__": main()
