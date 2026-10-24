#!/usr/bin/env python3
"""Chronological UFC forecast evaluation. Requires timestamped pre-fight predictions."""
import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

def timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)

def evaluate(rows):
    ordered=sorted(rows,key=lambda r: timestamp(r["fight_time"]))
    seen=set()
    evaluated=[]
    for row in ordered:
        fid=row["fight_id"]
        if fid in seen: raise ValueError("duplicate fight_id")
        seen.add(fid)
        p=float(row["predicted_red_win"])
        y=int(row["red_won"])
        if not (0<p<1 and y in (0,1)): raise ValueError("invalid probability/outcome")
        if timestamp(row["prediction_time"])>=timestamp(row["fight_time"]):
            raise ValueError("prediction generated after fight started: "+fid)
        if not row.get("model_version"):raise ValueError("missing model_version")
        evaluated.append((p,y))
    if not evaluated:raise ValueError("no valid chronological pre-fight predictions")
    n=len(evaluated)
    brier=sum((p-y)**2 for p,y in evaluated)/n
    logloss=-sum(y*math.log(p)+(1-y)*math.log1p(-p) for p,y in evaluated)/n
    accuracy=sum((p>=.5)==bool(y) for p,y in evaluated)/n
    buckets=[]
    for lo in range(0,10,2):
        group=[(p,y) for p,y in evaluated if lo/10<=p<(lo+2)/10 or (lo==8 and p==1)]
        if group:buckets.append({"range":f"{lo/10:.1f}-{(lo+2)/10:.1f}","n":len(group),"mean_prediction":sum(p for p,_ in group)/len(group),"win_rate":sum(y for _,y in group)/len(group)})
    return {"sample_size":n,"brier":brier,"log_loss":logloss,"accuracy":accuracy,
            "baseline_brier_50pct":sum((.5-y)**2 for _,y in evaluated)/n,
            "baseline_log_loss_50pct":math.log(2),"calibration_buckets":buckets,
            "interpretation":"Retrospective scores only. No proof of leakage-free training or positive betting EV."}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("csv_path",type=Path,help="CSV with fight_id,fight_time,prediction_time,model_version,predicted_red_win,red_won")
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    with args.csv_path.open(newline="") as f: result=evaluate(list(csv.DictReader(f)))
    text=json.dumps(result,indent=2)
    if args.output:args.output.write_text(text+"\n")
    print(text)

if __name__=="__main__":main()
