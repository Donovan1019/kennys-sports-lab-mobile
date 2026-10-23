#!/usr/bin/env python3
"""UFC reliability diagrams and ECE diagnostics for archived, pre-fight predictions.
Descriptive audit only; no training on evaluation results or betting authorization.
"""
import argparse
import json
import math
from pathlib import Path

def reliability(rows,bins=10,min_samples=100):
    if not isinstance(rows,list):
        raise ValueError("Rows must be a list")
    if not isinstance(bins,int) or not 2<=bins<=30:
        raise ValueError("Invalid bin count")
    if not isinstance(min_samples,int) or min_samples<1:
        raise ValueError("Invalid minimum sample count")
    valid=[]
    seen=set()
    rejected=0
    for row in rows:
        if not isinstance(row,dict):
            rejected+=1;continue
        fid=row.get("fight_id")
        p=row.get("red_win_probability")
        y=row.get("red_won")
        if not isinstance(fid,str) or not fid or fid in seen or isinstance(p,bool) or not isinstance(p,(int,float)) or not math.isfinite(p) or not 0<p<1 or type(y) is not bool or row.get("prefight_verified") is not True:
            rejected+=1;continue
        seen.add(fid)
        valid.append((p,int(y)))
    n=len(valid)
    buckets=[[] for _ in range(bins)]
    for p,y in valid:
        idx=min(int(p*bins),bins-1)
        buckets[idx].append((p,y))
    data=[]
    ece=0
    for i,bucket in enumerate(buckets):
        count=len(bucket)
        predicted=sum(p for p,_ in bucket)/count if count else None
        observed=sum(y for _,y in bucket)/count if count else None
        if count:
            ece+=count/n*abs(predicted-observed)
        data.append({"lower":i/bins,"upper":(i+1)/bins,"n":count,
                     "mean_predicted":predicted,"observed_win_rate":observed})
    brier=sum((p-y)**2 for p,y in valid)/n if n else None
    return {"sport":"UFC","schema":1,"graded":n,"rejected":rejected,
            "brier":brier,"expected_calibration_error":ece if n else None,
            "bins":data,"status":"INSUFFICIENT_SAMPLE" if n<min_samples else "REQUIRES_INDEPENDENT_REVIEW",
            "bet_eligible":False,"limitations":["Requires independently verified pre-fight predictions and completed results",
              "ECE depends on binning and can be unstable for small samples",
              "No confidence interval, price edge, or prospective validation established"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",default="backtests/reports/ufc_reliability.json")
    args=p.parse_args()
    payload=json.loads(Path(args.input).read_text())
    report=reliability(payload["graded_predictions"])
    output=Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+"\n")
    print(f"UFC reliability: {report['graded']} graded, status {report['status']}")
if __name__=="__main__":main()
