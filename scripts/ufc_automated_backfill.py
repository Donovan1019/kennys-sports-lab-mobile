#!/usr/bin/env python3
"""Select and execute a bounded UFC history batch; resume from committed checkpoints."""
import datetime as dt
import json
from pathlib import Path
from scripts.ufc_historical_backfill import backfill

PATH=Path("feed/ufc_historical_backfill.json")
START=dt.date(2024,1,1)
BATCH_DAYS=90

def select_days(existing,today):
    completed=set(existing.get("successful_days",[]))
    end=today-dt.timedelta(days=1)
    # Query 90 older dates per daily run; this reduces the multi-year backfill
    # from months to roughly two weeks at the expense of more public requests.
    # Always revisit the last 7 days to catch late-settling results, without
    # falsely treating a successful empty response as a confirmed complete card.
    recent=[end-dt.timedelta(days=i) for i in range(7)]
    missing=[]
    day=START
    while day<=end and len(missing)<BATCH_DAYS:
        if day.isoformat() not in completed:
            missing.append(day)
        day+=dt.timedelta(days=1)
    return sorted(set(missing+recent)) if missing else sorted(set(recent))

def run(existing,today,fetcher,checkpoint=None):
    days=select_days(existing,today)
    current=existing
    for day in days:
        # Retry recent dates by dropping them from the checkpoint before refresh.
        if day>=today-dt.timedelta(days=7):
            current=dict(current)
            current["successful_days"]=[x for x in current.get("successful_days",[]) if x!=day.isoformat()]
        current=backfill(day,day,current,fetcher=fetcher)
        if checkpoint is not None:
            checkpoint(current)
    return current

def main():
    prior=json.loads(PATH.read_text()) if PATH.exists() else {}
    def checkpoint(result):
        PATH.parent.mkdir(parents=True,exist_ok=True)
        temp=PATH.with_suffix(".tmp")
        temp.write_text(json.dumps(result,indent=2)+"\n")
        temp.replace(PATH)
    result=run(prior,dt.datetime.now(dt.timezone.utc).date(),__import__("scripts.ufc_historical_source",fromlist=["fetch_day"]).fetch_day,checkpoint=checkpoint)
    print("Verified fights:",result["verified_fights"],"successful days:",len(result["successful_days"]))
if __name__=="__main__":main()
