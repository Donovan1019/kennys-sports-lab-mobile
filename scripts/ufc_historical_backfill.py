#!/usr/bin/env python3
"""Incremental UFC historical scoreboard backfill with checkpoint and coverage audit.
Runs on demand; never treats absent events or missing methods as verified negatives.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
from scripts.ufc_historical_source import fetch_day,parse_day

def backfill(start,end,existing=None,fetcher=fetch_day):
    if end<start or end>=dt.datetime.now(dt.timezone.utc).date():
        raise ValueError("Date range must end before current UTC day")
    if (end-start).days>365:
        raise ValueError("Limit each run to 366 days")
    prior=existing or {}
    prior_results=prior.get("results",[])
    prior_days=set(prior.get("successful_days",[]))
    if not isinstance(prior_results,list):
        raise ValueError("Existing results must be a list")
    unique={}
    for r in prior_results:
        if isinstance(r,dict) and r.get("event_id") and r.get("fight_id"):
            unique[(str(r["event_id"]),str(r["fight_id"]))]=r
    errors=[]
    queried=0
    day=start
    while day<=end:
        label=day.isoformat()
        if label not in prior_days:
            try:
                data=fetcher(day)
                if not isinstance(data,dict) or not isinstance(data.get("events"),list):
                    raise ValueError("Unexpected scoreboard response; do not mark day complete")
                for r in parse_day(data,day):
                    key=(str(r["event_id"]),str(r["fight_id"]))
                    old=unique.get(key)
                    if old is None or (old.get("method") is None and r.get("method") is not None):
                        unique[key]=r
                prior_days.add(label)
                queried+=1
            except (OSError,ValueError,TypeError,KeyError) as exc:
                errors.append({"day":label,"reason":str(exc)})
        day+=dt.timedelta(days=1)
    return {"schema":1,"sport":"UFC","source":"ESPN public UFC scoreboard",
            "results":sorted(unique.values(),key=lambda r:(r.get("event_date",""),r["event_id"],r["fight_id"])),
            "successful_days":sorted(prior_days),"failed_days":errors,
            "newly_queried_days":queried,"verified_fights":len(unique),
            "bet_eligible":False,"limitations":["Public scoreboard may omit events and incomplete methods",
                "Successful request does not prove event coverage",
                "Fighter identity aliases and weight classes not reconciled",
                "No pre-fight odds, archived forecasts or independently validated edge"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--start",required=True)
    p.add_argument("--end",required=True)
    p.add_argument("--output",default="feed/ufc_historical_backfill.json")
    a=p.parse_args()
    start,end=dt.date.fromisoformat(a.start),dt.date.fromisoformat(a.end)
    out=Path(a.output)
    existing=json.loads(out.read_text()) if out.exists() else None
    result=backfill(start,end,existing)
    out.parent.mkdir(parents=True,exist_ok=True)
    temp=out.with_suffix(out.suffix+".tmp")
    temp.write_text(json.dumps(result,indent=2)+"\n")
    temp.replace(out)
    print(f"Verified fights: {result['verified_fights']}; newly queried days: {result['newly_queried_days']}; failed days: {len(result['failed_days'])}")
if __name__=="__main__":main()
