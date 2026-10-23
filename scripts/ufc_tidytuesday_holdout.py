#!/usr/bin/env python3
"""Strict chronological UFC Elo holdout audit with neutral-prior benchmark."""
import argparse
import datetime as dt
import json
import math
from pathlib import Path

def score(probabilities):
    n=len(probabilities)
    if not n:
        return {"n":0,"brier":None,"log_loss":None}
    return {"n":n,"brier":sum((1-p)**2 for p in probabilities)/n,
            "log_loss":sum(-math.log(max(1e-12,min(1-1e-12,p))) for p in probabilities)/n}

def audit(report, fraction=0.2, minimum_holdout=100):
    if report.get("bet_eligible") is not False or report.get("independently_verified") is not False:
        raise ValueError("Expected research-only unverified historical report")
    forecasts=report.get("forecasts",[])
    if not isinstance(forecasts,list) or not 0<fraction<0.5:
        raise ValueError("Invalid forecasts or holdout fraction")
    rows=[]
    for item in forecasts:
        if not isinstance(item,dict) or item.get("bet_eligible") is not False:
            raise ValueError("Forecast integrity failure")
        date=dt.date.fromisoformat(item["date"])
        prob=item["winner_probability"]
        if type(prob) not in (float,int) or not math.isfinite(prob) or not 0<prob<1:
            raise ValueError("Invalid forecast probability")
        rows.append((date,str(item["fight_url"]),prob))
    rows.sort()
    days=sorted({x[0] for x in rows})
    cut=max(1,int(len(days)*(1-fraction))) if days else 0
    holdout_start=days[cut] if cut<len(days) else None
    train=[x[2] for x in rows if holdout_start is None or x[0]<holdout_start]
    holdout=[x[2] for x in rows if holdout_start is not None and x[0]>=holdout_start]
    train_score=score(train)
    holdout_score=score(holdout)
    neutral={"brier":0.25,"log_loss":math.log(2)}
    enough=len(holdout)>=minimum_holdout
    return {"schema":1,"sport":"UFC","method":"chronological_date_holdout",
            "holdout_start":holdout_start.isoformat() if holdout_start else None,
            "train":train_score,"holdout":holdout_score,
            "neutral_baseline":neutral,
            "holdout_brier_improvement":(neutral["brier"]-holdout_score["brier"]) if holdout else None,
            "holdout_log_loss_improvement":(neutral["log_loss"]-holdout_score["log_loss"]) if holdout else None,
            "minimum_holdout":minimum_holdout,
            "enough_holdout":enough,"bet_eligible":False,
            "status":"RESEARCH_ONLY" if enough else "INSUFFICIENT_HOLDOUT",
            "limitations":["The holdout is an evaluation slice of one frozen historical run, not an independently retrained model",
                           "Source result records and feature timing are not independently verified",
                           "No timestamp-verified bookmaker odds or profit evaluation",
                           "No prospective validation or betting approval"]}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",default="backtests/reports/ufc_tidytuesday_elo.json")
    parser.add_argument("--output",default="backtests/reports/ufc_tidytuesday_holdout.json")
    args=parser.parse_args()
    report=audit(json.loads(Path(args.input).read_text()))
    output=Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+"\n")
    print("UFC holdout:",report["holdout"]["n"],"Brier:",report["holdout"]["brier"],
          "neutral:",report["neutral_baseline"]["brier"])

if __name__=="__main__":
    main()
