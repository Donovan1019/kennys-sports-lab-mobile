#!/usr/bin/env python3
"""Build UFC historical features using ONLY prior completed bouts.

Input must contain one row per fighter per fight, with immutable fight identifiers,
start times, settled status, and landed/attempted counts. No same-fight rows enter
pre-fight features. Source publication/capture provenance must be validated
separately before using historical snapshots for a betting backtest.
"""
import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

def stamp(value):
    dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    if dt.tzinfo is None:raise ValueError("naive timestamp")
    return dt.astimezone(timezone.utc)

def build(rows):
    grouped=defaultdict(list)
    seen=set()
    for r in rows:
        fid=str(r["fight_id"]).strip()
        fighter=str(r["fighter_id"]).strip()
        if not fid or not fighter:raise ValueError("blank identifiers")
        if (fid,fighter) in seen:raise ValueError("duplicate fighter/fight row")
        seen.add((fid,fighter))
        if str(r["settled"]).lower() not in ("true","false"):
            raise ValueError("settled must be true or false")
        for field in ("sig_landed","sig_attempted","takedowns_landed","takedowns_attempted","active_seconds"):
            value=float(r[field])
            if not (0<=value<1e7):raise ValueError("invalid count: "+field)
        if float(r["sig_landed"])>float(r["sig_attempted"]) or float(r["takedowns_landed"])>float(r["takedowns_attempted"]):
            raise ValueError("landed exceeds attempted")
        grouped[fighter].append(r)
    output=[]
    for fighter,history in grouped.items():
        history.sort(key=lambda r:(stamp(r["fight_time"]),r["fight_id"]))
        prior=[]
        for r in history:
            start=stamp(r["fight_time"])
            eligible=[p for p in prior if stamp(p["fight_time"])<start and str(p["settled"]).lower()=="true"]
            seconds=sum(float(p["active_seconds"]) for p in eligible)
            entry={"fight_id":r["fight_id"],"fighter_id":fighter,"fight_time":r["fight_time"],
                   "prior_fights":len(eligible),"prior_active_seconds":seconds,
                   "sig_landed_per_min":(60*sum(float(p["sig_landed"]) for p in eligible)/seconds if seconds>0 else None),
                   "sig_accuracy":(sum(float(p["sig_landed"]) for p in eligible)/sum(float(p["sig_attempted"]) for p in eligible) if sum(float(p["sig_attempted"]) for p in eligible)>0 else None),
                   "takedowns_per_15min":(900*sum(float(p["takedowns_landed"]) for p in eligible)/seconds if seconds>0 else None)}
            output.append(entry)
            prior.append(r)
    return sorted(output,key=lambda x:(stamp(x["fight_time"]),x["fight_id"],x["fighter_id"]))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("rows_csv",type=Path)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    with args.rows_csv.open(newline="") as f:rows=list(csv.DictReader(f))
    result=build(rows)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print("Pre-fight fighter rows:",len(result))

if __name__=="__main__":main()
