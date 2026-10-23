#!/usr/bin/env python3
"""Research-only chronological Elo over unverified TidyTuesday historical results.

Never mixes snapshot results with independently verified production history.
Same-day bouts are predicted from prior-day ratings before any day's updates.
"""
import argparse
import datetime as dt
import json
import math
from collections import defaultdict
from pathlib import Path

def build(snapshot, k=24, min_bouts=5):
    if snapshot.get("bet_eligible") is not False or snapshot.get("snapshot") != "2026-07-07":
        raise ValueError("Unexpected or betting-enabled historical snapshot")
    fights=snapshot.get("fight_history",{}).get("rows",[])
    by_day=defaultdict(list)
    seen=set()
    for row in fights:
        if not isinstance(row,dict) or row.get("independently_verified") is not False:
            continue
        try:
            date=dt.date.fromisoformat(row["event_date"])
            winner,loser=row["winner"],row["loser"]
            key=row["source_fight_url"]
        except (KeyError,ValueError,TypeError):
            continue
        if not winner or not loser or winner==loser or key in seen:
            continue
        seen.add(key)
        by_day[date].append((key,winner,loser))
    ratings={}
    bouts={}
    predictions=[]
    for day in sorted(by_day):
        updates=defaultdict(float)
        increments=defaultdict(int)
        for key,winner,loser in by_day[day]:
            rw=ratings.get(winner,1500.)
            rl=ratings.get(loser,1500.)
            prob=1/(1+10**((rl-rw)/400))
            if bouts.get(winner,0)>=min_bouts and bouts.get(loser,0)>=min_bouts:
                predictions.append({"date":day.isoformat(),"fight_url":key,"winner":winner,
                                    "loser":loser,"winner_probability":prob,
                                    "pre_event_prediction":True,"bet_eligible":False})
            delta=k*(1-prob)
            updates[winner]+=delta
            updates[loser]-=delta
            increments[winner]+=1
            increments[loser]+=1
        for fighter,delta in updates.items():
            ratings[fighter]=ratings.get(fighter,1500.)+delta
            bouts[fighter]=bouts.get(fighter,0)+increments[fighter]
    n=len(predictions)
    return {"schema":1,"sport":"UFC","source":"TidyTuesday 2026-07-07 historical snapshot",
            "research_only":True,"bet_eligible":False,
            "independently_verified":False,"historical_bouts_used":len(seen),
            "pre_event_evaluated_fights":n,
            "brier":sum((1-r["winner_probability"])**2 for r in predictions)/n if n else None,
            "log_loss":sum(-math.log(r["winner_probability"]) for r in predictions)/n if n else None,
            "ratings":{name:{"elo":round(value,2),"historical_bouts":bouts[name]}
                       for name,value in sorted(ratings.items())},
            "forecasts":predictions,
            "limitations":["Snapshot results have not been independently verified",
                           "No same-day fight outcome leakage; same-day bouts share prior-day ratings",
                           "Historical data may have incomplete coverage",
                           "No approved out-of-sample calibration or timestamped odds"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="feed/ufc_tidytuesday_research.json")
    p.add_argument("--output",default="backtests/reports/ufc_tidytuesday_elo.json")
    args=p.parse_args()
    report=build(json.loads(Path(args.input).read_text()))
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print("Historical UFC Elo:",report["historical_bouts_used"],"bouts;",report["pre_event_evaluated_fights"],"evaluated")

if __name__=="__main__":
    main()
