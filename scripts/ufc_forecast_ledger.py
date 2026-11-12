#!/usr/bin/env python3
"""Append-only UFC pre-fight forecast ledger; never overwrites existing fight/version forecasts."""
import argparse
import csv
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

FIELDS=["fight_id","fight_time","prediction_time","model_version","predicted_red_win","red_won"]
def parse_time(s):
    d=datetime.fromisoformat(s.replace("Z","+00:00"))
    if d.tzinfo is None:raise ValueError("timestamps must include timezone")
    return d.astimezone(timezone.utc)
def append_forecasts(path,rows):
    path=Path(path)
    existing=[]
    if path.exists():
        with path.open(newline="") as f:existing=list(csv.DictReader(f))
    keys={(r["fight_id"],r["model_version"]) for r in existing}
    fresh=[]
    now=datetime.now(timezone.utc)
    for row in rows:
        if not all(row.get(k) not in (None,"") for k in FIELDS[:-1]):raise ValueError("missing required forecast field")
        p=float(row["predicted_red_win"])
        if not math.isfinite(p) or not 0<p<1:raise ValueError("invalid forecast probability")
        if parse_time(row["prediction_time"])>now:raise ValueError("future prediction timestamp")
        if parse_time(row["prediction_time"])>=parse_time(row["fight_time"]):raise ValueError("forecast not pre-fight")
        key=(str(row["fight_id"]),str(row["model_version"]))
        if key in keys:raise ValueError("duplicate forecast key "+repr(key))
        keys.add(key)
        fresh.append({k:str(row.get(k,"")) for k in FIELDS})
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS)
        if not existing:writer.writeheader()
        writer.writerows(fresh)
    return len(fresh)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ledger",type=Path,required=True)
    ap.add_argument("--input",type=Path,required=True,help="JSON array of immutable pre-fight forecast records")
    args=ap.parse_args()
    rows=json.loads(args.input.read_text())
    if not isinstance(rows,list):raise ValueError("input must be array")
    print("appended",append_forecasts(args.ledger,rows),"forecasts")

if __name__=="__main__":main()
