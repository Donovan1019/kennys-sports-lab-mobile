#!/usr/bin/env python3
"""Leakage-conscious UFC opponent-differential walk-forward research benchmark.

No model is fitted on a test fight or a later fight. Same-day fights are
predicted as a batch before any same-day outcomes enter model training.
Retrospective dataset: NOT point-in-time certified or betting-ready.
"""
import argparse,hashlib,json,math
from collections import defaultdict
from datetime import date
from pathlib import Path
from scripts.ufc_native_fight_join import BASE,fetch,join
from scripts.ufc_joined_chronological_rows import convert
from scripts.ufc_historical_prefix_features import build as prefix

FIELDS=("sig_landed_per_min","sig_accuracy","takedowns_per_15min")
SCALE=(4.0,0.5,3.0)
def sigmoid(z):
    z=max(-35,min(35,z))
    return 1/(1+math.exp(-z))
def vector(a,b):
    if a["prior_fights"]<2 or b["prior_fights"]<2:return None
    if any(a[k] is None or b[k] is None for k in FIELDS):return None
    # Bounded, deterministic predeclared feature scaling; no test-set fitting.
    return [max(-3,min(3,(a[k]-b[k])/scale)) for k,scale in zip(FIELDS,SCALE)]
def examples(records,feature_rows):
    bykey={(r["fight_id"],r["fighter_id"]):r for r in feature_rows}
    output=[];excluded=defaultdict(int)
    for record in records:
        f=record["wide_record"]
        fid=record["ufcstats_fight_id"]
        a=bykey.get((fid,record["fighter_1_ufcstats_id"]))
        b=bykey.get((fid,record["fighter_2_ufcstats_id"]))
        if not a or not b:excluded["missing_fighter_history"]+=1;continue
        x=vector(a,b)
        if x is None:excluded["insufficient_prior_history"]+=1;continue
        # Winner must be an exact source-native fighter ID, never a guessed corner.
        winner=str(f.get("winner","")).strip().lower()
        f1=record["fighter_1_ufcstats_id"]
        f2=record["fighter_2_ufcstats_id"]
        if winner not in (f1,f2):
            excluded["winner_not_native_fighter_id"]+=1;continue
        output.append({"fight_id":fid,"date":a["fight_time"][:10],"x":x,
                       "y":int(winner==f1)})
    return sorted(output,key=lambda r:(r["date"],r["fight_id"])),dict(excluded)
def evaluate(rows,train_fraction=.7,lr=.04,reg=.0005):
    if not .5<=train_fraction<1:raise ValueError("invalid split")
    days=sorted(set(r["date"] for r in rows))
    if len(days)<4:raise ValueError("not enough independent event days")
    cutoff=days[max(1,min(len(days)-1,int(len(days)*train_fraction)))]
    weights=[0.0]*4
    predictions=[]
    train_n=0
    grouped=defaultdict(list)
    for r in rows:grouped[r["date"]].append(r)
    for day in days:
        batch=grouped[day]
        # Predictions precede updates: prevents within-event outcome leakage.
        for r in batch:
            z=weights[0]+sum(w*x for w,x in zip(weights[1:],r["x"]))
            p=sigmoid(z)
            if day>=cutoff:predictions.append((p,r["y"],r["fight_id"],day))
        if day<cutoff:
            for r in batch:
                x=[1.0]+r["x"]
                p=sigmoid(sum(w*v for w,v in zip(weights,x)))
                for i in range(4):
                    weights[i]-=lr*((p-r["y"])*x[i]+(reg*weights[i] if i else 0))
                train_n+=1
    if not predictions:raise ValueError("no test predictions")
    n=len(predictions)
    brier=sum((p-y)**2 for p,y,_,_ in predictions)/n
    loss=-sum(y*math.log(max(p,1e-12))+(1-y)*math.log(max(1-p,1e-12)) for p,y,_,_ in predictions)/n
    return {"training_fights":train_n,"test_fights":n,"cutoff_date":cutoff,
       "test_brier":brier,"test_log_loss":loss,
       "test_accuracy":sum((p>=.5)==bool(y) for p,y,_,_ in predictions)/n,
       "baseline_brier_50pct":.25,"baseline_log_loss_50pct":math.log(2),
       "weights":weights,"bet_eligible":False,
       "provenance":"RETROSPECTIVE_NOT_PIT_CERTIFIED",
       "limitations":"No historical source capture timestamps; no market odds or profitability verification."}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    cross,_=fetch(BASE+"id_crosswalk_all.csv")
    wide,_=fetch(BASE+"ufc_all_fights_wide.csv")
    linked=join(cross,wide)
    if linked["status"]!="JOINED":raise SystemExit("ID join failed")
    fighter=convert(linked["records"])
    features=prefix(fighter["rows"])
    rows,excluded=examples(linked["records"],features)
    if len(rows)<100:raise SystemExit("Insufficient source-native settled training examples: "+json.dumps(excluded))
    result=evaluate(rows)
    result["eligible_examples"]=len(rows)
    result["excluded"]=excluded
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
