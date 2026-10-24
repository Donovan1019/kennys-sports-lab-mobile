#!/usr/bin/env python3
"""Leakage-conscious chronological count-rate holdout, retrospective research only."""
import argparse,json,math
from collections import defaultdict
from pathlib import Path
from scripts.ufc_native_fight_join import BASE,fetch,join
from scripts.ufc_joined_chronological_rows import convert

MARKETS=("sig_landed","sig_attempted","takedowns_landed","takedowns_attempted")
def evaluate(rows,min_prior=3,train_fraction=.8):
    if not 0<train_fraction<1:raise ValueError("invalid split")
    fights=defaultdict(list)
    for r in rows:fights[str(r["fight_id"])].append(r)
    dated=[]
    for fid,group in fights.items():
        if len(group)!=2 or len(set(r["fighter_id"] for r in group))!=2:raise ValueError("invalid paired fight")
        if len(set(r["fight_time"] for r in group))!=1:raise ValueError("conflicting fight dates")
        if len(set(r["active_seconds"] for r in group))!=1:raise ValueError("conflicting fight durations")
        dated.append((group[0]["fight_time"][:10],fid,group))
    dated.sort()
    if len(dated)<10:raise ValueError("insufficient fights")
    cutoff=dated[int(len(dated)*train_fraction)][0]
    if cutoff==dated[0][0]:raise ValueError("no earlier-date training fights for holdout")
    history=defaultdict(list);metrics=defaultdict(list);excluded=defaultdict(int)
    for day in sorted(set(x[0] for x in dated)):
        batch=[x for x in dated if x[0]==day]
        for _,fid,group in batch:
            for row in group:
                h=history[row["fighter_id"]]
                if day<cutoff:continue
                if len(h)<min_prior:
                    excluded["insufficient_prior_fights"]+=1;continue
                exposure=sum(float(v["active_seconds"]) for v in h)
                if exposure<=0:
                    excluded["invalid_exposure"]+=1;continue
                for key in MARKETS:
                    rate=sum(float(v[key]) for v in h)/exposure
                    actual=float(row[key])
                    # Known realized duration is diagnostic oracle, not a pre-fight feature.
                    expected=rate*float(row["active_seconds"])
                    metrics[key].append((expected,actual,fid))
        for _,_,group in batch:
            for row in group:
                if str(row["settled"]).lower()=="true":history[row["fighter_id"]].append(row)
    report={}
    for key,items in metrics.items():
        n=len(items)
        if not n:continue
        report[key]={"n":n,"distinct_fights":len(set(v[2] for v in items)),
          "mae":sum(abs(p-y) for p,y,_ in items)/n,
          "rmse":math.sqrt(sum((p-y)**2 for p,y,_ in items)/n),
          "bias":sum(p-y for p,y,_ in items)/n,
          "mean_predicted":sum(p for p,_,_ in items)/n,
          "mean_observed":sum(y for _,y,_ in items)/n}
    return {"schema":1,"holdout_start_date":cutoff,"markets":report,"excluded":dict(excluded),
      "method":"prior-date per-second fighter rate multiplied by observed duration",
      "source_point_in_time_certified":False,"duration_oracle":True,
      "bet_eligible":False,"calibrated":False,
      "limitations":"Held-out dates are never used to train future model coefficients, but earlier holdout bouts update fighter histories. Realized fight duration is an oracle and is not available pre-fight. Retrospective data publication timing unverified; not a betting backtest."}
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    cross,_=fetch(BASE+"id_crosswalk_all.csv");wide,_=fetch(BASE+"ufc_all_fights_wide.csv")
    joined=join(cross,wide)
    if joined["status"]!="JOINED":raise SystemExit("Fight ID join failed")
    report=evaluate(convert(joined["records"])["rows"])
    if not report["markets"]:raise SystemExit("No eligible holdout observations")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v["n"] for k,v in report["markets"].items()}))
if __name__=="__main__":main()
