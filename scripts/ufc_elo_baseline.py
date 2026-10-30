#!/usr/bin/env python3
"""Chronological UFC Elo baseline: opponent-adjusted winner predictions.
Research only until verified data coverage, holdout calibration and sportsbook lines.
"""
import argparse
import datetime as dt
import json
import math
from pathlib import Path

def parse_time(value):
    t=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    if t.tzinfo is None:
        raise ValueError("Timezone required")
    return t.astimezone(dt.timezone.utc)

def build(rows,k=24,minimum_history=5):
    if not isinstance(rows,list):
        raise ValueError("Historical results must be a list")
    if not 0<k<=100 or not isinstance(minimum_history,int) or minimum_history<1:
        raise ValueError("Invalid Elo parameters")
    eligible=[]
    for row in rows:
        if not isinstance(row,dict) or row.get("winner_verified") is not True:
            continue
        try:
            winner,loser=row["winner"].strip(),row["loser"].strip()
            event_id,fight_id=row["event_id"],row["fight_id"]
            t=parse_time(row["event_date"])
            if not winner or not loser or winner==loser or not event_id or not fight_id:
                continue
        except (KeyError,ValueError,TypeError,AttributeError):
            continue
        eligible.append((t,str(event_id),str(fight_id),winner,loser))
    eligible.sort()
    ratings={}
    bouts={}
    seen=set()
    forecasts=[]
    for t,eid,fid,winner,loser in eligible:
        key=(eid,fid)
        if key in seen:
            continue
        seen.add(key)
        rw=ratings.get(winner,1500.0)
        rl=ratings.get(loser,1500.0)
        probability=1/(1+10**((rl-rw)/400))
        # Predict before updating; no future outcome leakage.
        if bouts.get(winner,0)>=minimum_history and bouts.get(loser,0)>=minimum_history:
            forecasts.append({"fight_id":fid,"event_id":eid,"start_time":t.isoformat(),
                              "winner":winner,"loser":loser,"winner_probability":probability,
                              "model_version":"ufc-elo-baseline-v1","research_only":True,"bet_eligible":False})
        delta=k*(1-probability)
        ratings[winner]=rw+delta
        ratings[loser]=rl-delta
        bouts[winner]=bouts.get(winner,0)+1
        bouts[loser]=bouts.get(loser,0)+1
    n=len(forecasts)
    baseline_brier=0.25 if n else None
    baseline_log_loss=math.log(2) if n else None
    brier=sum((1-x["winner_probability"])**2 for x in forecasts)/n if n else None
    loss=sum(-math.log(x["winner_probability"]) for x in forecasts)/n if n else None
    improvement_brier=(baseline_brier-brier)/baseline_brier if n else None
    return {"schema":1,"sport":"UFC","model_version":"ufc-elo-baseline-v1",
            "historical_bouts_used":len(seen),"pre_update_evaluated_fights":n,
            "brier":brier,"log_loss":loss,"baseline_brier":baseline_brier,"baseline_log_loss":baseline_log_loss,"brier_skill_vs_50pct":improvement_brier,"minimum_prior_bouts_per_fighter":minimum_history,
            "ratings":{name:{"elo":round(ratings[name],2),"historical_bouts":bouts[name]}
                       for name in sorted(ratings)},"forecasts":forecasts,
            "bet_eligible":False,"calibration_status":"INSUFFICIENT_SAMPLE" if n<100 else "REQUIRES_INDEPENDENT_HOLDOUT",
            "limitations":["Historical fights evaluated chronologically but same-event order may be uncertain",
                           "No fighter inactivity, age, weight class, injuries, or style adjustments",
                           "No archived odds or independent holdout validation"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",default="backtests/reports/ufc_elo_baseline.json")
    args=p.parse_args()
    rows=json.loads(Path(args.input).read_text())["results"]
    report=build(rows)
    output=Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+"\n")
    print(f"UFC Elo: {report['historical_bouts_used']} historical bouts, {report['pre_update_evaluated_fights']} pre-update evaluations")
if __name__=="__main__":
    main()
