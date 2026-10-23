#!/usr/bin/env python3
"""Tune UFC Elo only on pre-holdout fights; evaluate the locked winner once."""
import argparse
import datetime as dt
import json
import math
from collections import defaultdict
from pathlib import Path

def split_fights(snapshot, holdout_start):
    if snapshot.get("bet_eligible") is not False:
        raise ValueError("Research-only snapshot required")
    grouped=defaultdict(list)
    seen=set()
    for row in snapshot.get("fight_history",{}).get("rows",[]):
        try:
            date=dt.date.fromisoformat(row["event_date"])
            key=row["source_fight_url"]
            w,l=row["winner"],row["loser"]
        except (KeyError,ValueError,TypeError):
            continue
        if row.get("independently_verified") is not False or not key or key in seen or not w or not l or w==l:
            continue
        seen.add(key)
        grouped[date].append((w,l))
    return grouped

def run_elo(grouped, k, minimum_history):
    ratings,bouts={},{}
    evaluated=[]
    for day in sorted(grouped):
        deltas=defaultdict(float)
        increments=defaultdict(int)
        for winner,loser in grouped[day]:
            rw,rl=ratings.get(winner,1500.),ratings.get(loser,1500.)
            p=1/(1+10**((rl-rw)/400))
            if bouts.get(winner,0)>=minimum_history and bouts.get(loser,0)>=minimum_history:
                evaluated.append((day,p))
            d=k*(1-p)
            deltas[winner]+=d
            deltas[loser]-=d
            increments[winner]+=1
            increments[loser]+=1
        for fighter,d in deltas.items():
            ratings[fighter]=ratings.get(fighter,1500.)+d
            bouts[fighter]=bouts.get(fighter,0)+increments[fighter]
    return evaluated

def metrics(probs):
    if not probs:
        return {"n":0,"brier":None,"log_loss":None}
    return {"n":len(probs),"brier":sum((1-p)**2 for p in probs)/len(probs),
            "log_loss":sum(-math.log(max(1e-12,p)) for p in probs)/len(probs)}

def tune(snapshot, holdout_start="2023-03-18"):
    cut=dt.date.fromisoformat(holdout_start)
    grouped=split_fights(snapshot,cut)
    candidates=[]
    for k in (8,16,24,32,48):
        for minimum_history in (3,5,8):
            evals=run_elo(grouped,k,minimum_history)
            train=metrics([p for day,p in evals if day<cut])
            candidates.append({"k":k,"minimum_history":minimum_history,"train":train})
    viable=[c for c in candidates if c["train"]["n"]>=500]
    if not viable:
        raise ValueError("Insufficient training history to tune Elo")
    best=min(viable,key=lambda c:(c["train"]["brier"],c["train"]["log_loss"],c["k"],c["minimum_history"]))
    evals=run_elo(grouped,best["k"],best["minimum_history"])
    holdout=metrics([p for day,p in evals if day>=cut])
    return {"schema":1,"sport":"UFC","method":"train_only_grid_search_then_locked_holdout",
            "holdout_start":holdout_start,"candidates":candidates,
            "selected":{"k":best["k"],"minimum_history":best["minimum_history"],"train":best["train"]},
            "holdout":holdout,"neutral_baseline":{"brier":0.25,"log_loss":math.log(2)},
            "holdout_brier_improvement":None if not holdout["n"] else 0.25-holdout["brier"],
            "bet_eligible":False,"research_only":True,
            "limitations":["The holdout date was selected in a previous experiment; results are not a fresh untouched prospective holdout",
                           "Hyperparameters selected using only fights before the holdout boundary",
                           "Snapshot results and odds not independently verified",
                           "No prospective betting calibration or independent price evaluation"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="feed/ufc_tidytuesday_research.json")
    p.add_argument("--output",default="backtests/reports/ufc_elo_tuned_holdout.json")
    p.add_argument("--holdout-start",default="2023-03-18")
    args=p.parse_args()
    report=tune(json.loads(Path(args.input).read_text()),args.holdout_start)
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print("Selected:",report["selected"]["k"],report["selected"]["minimum_history"],
          "holdout:",report["holdout"])

if __name__=="__main__":
    main()
