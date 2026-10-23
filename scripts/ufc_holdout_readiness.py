#!/usr/bin/env python3
"""UFC chronological holdout evaluation with explicit baseline and sample-size gates."""
import argparse
import datetime as dt
import json
import math
from pathlib import Path
from scripts.ufc_elo_baseline import build,parse_time

def evaluate(rows,holdout_fraction=.2,min_holdout=100,min_prior=5):
    if not 0<holdout_fraction<.5:
        raise ValueError("Holdout fraction must be between 0 and .5")
    if not isinstance(rows,list):
        raise ValueError("Results must be a list")
    ordered=[]
    for row in rows:
        if not isinstance(row,dict) or row.get("winner_verified") is not True:
            continue
        try:
            t=parse_time(row["event_date"])
            if not row["winner"] or not row["loser"] or row["winner"]==row["loser"]:
                continue
            ordered.append((t,row))
        except (ValueError,KeyError,TypeError):
            continue
    ordered.sort(key=lambda x:(x[0],str(x[1].get("event_id")),str(x[1].get("fight_id"))))
    # Split by event timestamp, not individual fights, to avoid same-event crossover.
    dates=sorted(set(t for t,_ in ordered))
    if len(dates)<2:
        return {"status":"INSUFFICIENT_HISTORY","bet_eligible":False,"holdout_n":0}
    split_index=max(1,int(len(dates)*(1-holdout_fraction)))
    if split_index>=len(dates):
        return {"status":"INSUFFICIENT_HISTORY","bet_eligible":False,"holdout_n":0}
    cutoff=dates[split_index]
    train=[row for t,row in ordered if t<cutoff]
    full=build([row for _,row in ordered],minimum_history=min_prior)
    holdout_ids={(str(row.get("event_id")),str(row.get("fight_id"))) for t,row in ordered if t>=cutoff}
    holdout=[p for p in full["forecasts"] if (p["event_id"],p["fight_id"]) in holdout_ids]
    n=len(holdout)
    brier=sum((1-p["winner_probability"])**2 for p in holdout)/n if n else None
    loss=sum(-math.log(p["winner_probability"]) for p in holdout)/n if n else None
    return {"status":"INSUFFICIENT_HOLDOUT" if n<min_holdout else "REQUIRES_INDEPENDENT_REVIEW",
            "train_rows":len(train),"holdout_n":n,"cutoff":cutoff.isoformat(),
            "brier":brier,"log_loss":loss,"coinflip_brier":.25,"coinflip_log_loss":math.log(2),
            "beats_coinflip_brier":brier<.25 if brier is not None else None,
            "bet_eligible":False,
            "limitations":["Elo K-factor and minimum history must be frozen before true out-of-sample use",
                           "Holdout rows update Elo sequentially using previously settled holdout outcomes",
                           "Historical source completeness and identity verification not independently audited",
                           "No sportsbook odds, market calibration, or ROI proof"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",default="backtests/reports/ufc_holdout_readiness.json")
    args=p.parse_args()
    rows=json.loads(Path(args.input).read_text())["results"]
    report=evaluate(rows)
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(report["status"],"holdout_n",report["holdout_n"])
if __name__=="__main__":main()
