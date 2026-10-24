#!/usr/bin/env python3
"""Fail-closed join between UFC pre-fight labels and point-in-time feature records."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from scripts.ufc_point_in_time_gate import validate,parse_time

def assemble(labels,features):
    by_fight=defaultdict(list)
    for row in features:
        validate(row)
        by_fight[str(row["fight_id"])].append(row)
    output=[]
    seen=set()
    for label in labels:
        fid=str(label["fight_id"]).strip()
        if not fid or fid in seen:raise ValueError("missing or duplicate fight id")
        seen.add(fid)
        cutoff=parse_time(label["prediction_time"])
        start=parse_time(label["fight_time"])
        if cutoff>=start:raise ValueError("prediction cutoff after fight start")
        if str(label["red_won"]) not in ("0","1"):raise ValueError("invalid settled winner")
        rows=by_fight[fid]
        if not rows:raise ValueError("missing point-in-time features for "+fid)
        feat={}
        for row in rows:
            if parse_time(row["prediction_cutoff"])!=cutoff:
                raise ValueError("feature cutoff mismatch: "+fid)
            if parse_time(row["captured_at"])>cutoff:
                raise ValueError("post-cutoff capture: "+fid)
            name=str(row["fighter_id"])+":"+str(row["feature_name"])
            if name in feat:raise ValueError("duplicate feature: "+fid+" "+name)
            feat[name]=row["value"]
        output.append({"fight_id":fid,"prediction_time":label["prediction_time"],
                       "fight_time":label["fight_time"],"red_won":int(label["red_won"]),
                       "features":feat})
    return output

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--labels",type=Path,required=True)
    p.add_argument("--features",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    with a.labels.open(newline="") as f:labels=list(csv.DictReader(f))
    features=json.loads(a.features.read_text())
    output=assemble(labels,features)
    a.output.write_text(json.dumps(output,indent=2)+"\n")
    print("PIT-eligible training examples:",len(output))

if __name__=="__main__":main()
