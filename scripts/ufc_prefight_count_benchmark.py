#!/usr/bin/env python3
"""Chronological opponent-aware UFC count benchmark, historical-duration research, no realized-duration leakage."""
import argparse,json,math
from collections import defaultdict
from pathlib import Path
from scripts.ufc_native_fight_join import BASE,fetch,join
from scripts.ufc_joined_chronological_rows import convert
from scripts.ufc_count_holdout import MARKETS

def evaluate(rows,min_prior=3,train_fraction=.8,opponent_weight=.25):
    if not 0<train_fraction<1 or not 0<=opponent_weight<=1:raise ValueError("invalid parameters")
    fights=defaultdict(list)
    for row in rows:fights[str(row["fight_id"])].append(row)
    dated=[]
    for fid,group in fights.items():
        if len(group)!=2 or len({r["fighter_id"] for r in group})!=2:raise ValueError("invalid fighter pair")
        if len({r["fight_time"] for r in group})!=1 or len({r["active_seconds"] for r in group})!=1:
            raise ValueError("inconsistent paired fight")
        dated.append((group[0]["fight_time"][:10],fid,group))
    dated.sort()
    if len(dated)<10:raise ValueError("insufficient fights")
    cutoff=dated[int(len(dated)*train_fraction)][0]
    if cutoff==dated[0][0]:raise ValueError("no earlier-date training fights")
    offense=defaultdict(list);allowed=defaultdict(list);errors=defaultdict(list);excluded=defaultdict(int);duration_errors=[]
    for day in sorted({d for d,_,_ in dated}):
        batch=[x for x in dated if x[0]==day]
        for _,fid,group in batch:
            if day<cutoff:continue
            for fighter,opponent in ((group[0],group[1]),(group[1],group[0])):
                own=offense[fighter["fighter_id"]];opp=allowed[opponent["fighter_id"]]
                if len(own)<min_prior or len(opp)<min_prior:
                    excluded["insufficient_fighter_or_opponent_history"]+=1;continue
                own_exposure=sum(d for d,_ in own);opp_exposure=sum(d for d,_ in opp)
                # Pre-bout estimate: equal-weight fighter and opponent prior mean
                # fight durations. Never inspect this bout's realized duration.
                duration=.5*(own_exposure/len(own)+opp_exposure/len(opp))
                duration_errors.append((duration,float(fighter["active_seconds"])))
                if min(own_exposure,opp_exposure,duration)<=0:
                    excluded["invalid_exposure"]+=1;continue
                for key in MARKETS:
                    own_rate=sum(v[key] for _,v in own)/own_exposure
                    opponent_allowed_rate=sum(v[key] for _,v in opp)/opp_exposure
                    baseline=own_rate*duration
                    adjusted=((1-opponent_weight)*own_rate+opponent_weight*opponent_allowed_rate)*duration
                    actual=float(fighter[key])
                    errors[key].append((baseline,adjusted,actual,fid))
        for _,_,group in batch:
            for fighter,opponent in ((group[0],group[1]),(group[1],group[0])):
                if str(fighter["settled"]).lower()!="true":continue
                duration=float(fighter["active_seconds"])
                offense[fighter["fighter_id"]].append((duration,{k:float(fighter[k]) for k in MARKETS}))
                allowed[opponent["fighter_id"]].append((duration,{k:float(fighter[k]) for k in MARKETS}))
    metrics={}
    for key,items in errors.items():
        n=len(items)
        if not n:continue
        mae=lambda idx:sum(abs(v[idx]-v[2]) for v in items)/n
        rmse=lambda idx:math.sqrt(sum((v[idx]-v[2])**2 for v in items)/n)
        base=mae(0);adjusted=mae(1)
        metrics[key]={"n":n,"distinct_fights":len({v[3] for v in items}),
          "baseline_mae":base,"opponent_adjusted_mae":adjusted,
          "mae_improvement":base-adjusted,
          "baseline_rmse":rmse(0),"opponent_adjusted_rmse":rmse(1),
          "opponent_adjustment_outperforms_baseline":adjusted<base}
    return {"schema":1,"holdout_start_date":cutoff,"opponent_weight_fixed":opponent_weight,
       "markets":metrics,"excluded":dict(excluded),"oracle_duration":False,
       "duration_prediction_method":"mean of each fighter prior bout mean duration",
       "duration_mae_seconds":sum(abs(p-y) for p,y in duration_errors)/len(duration_errors) if duration_errors else None,
       "weight_tuned_on_holdout":False,"point_in_time_certified":False,
       "calibrated":False,"bet_eligible":False,
       "limitations":"Fixed illustrative blend weight not fitted. Same-date isolation; earlier holdout fights update histories. Duration predicted from prior bouts only; scheduled rounds unverified (3/5 mixed), retrospective capture timestamps unverified. This is not a point-in-time certified betting backtest."}
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);args=p.parse_args()
    cross,_=fetch(BASE+"id_crosswalk_all.csv");wide,_=fetch(BASE+"ufc_all_fights_wide.csv")
    linked=join(cross,wide)
    if linked["status"]!="JOINED":raise SystemExit("fight join failed")
    report=evaluate(convert(linked["records"])["rows"])
    if not report["markets"]:raise SystemExit("no eligible holdout observations")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v["n"] for k,v in report["markets"].items()}))
if __name__=="__main__":main()
