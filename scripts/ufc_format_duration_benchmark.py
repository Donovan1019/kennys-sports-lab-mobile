#!/usr/bin/env python3
"""Research-only pre-bout format-stratified UFC duration benchmark.

Uses scheduled_rounds as an experimental source field, NOT independently
verified pre-bout provenance. Holdout observations never enter same-day history.
"""
import argparse,json,math
from collections import defaultdict
from pathlib import Path
from scripts.ufc_native_fight_join import BASE,fetch,join

def evaluate(records,train_fraction=.8,min_prior=3):
    if not 0<train_fraction<1 or min_prior<1:raise ValueError("invalid parameters")
    fights=[]
    for record in records:
        f=record["wide_record"]
        if str(f.get("scheduled_rounds","")).strip() not in ("3","5"):continue
        try:
            duration=float(f["fight_duration_sec"])
            day=str(f["event_date"])[:10]
            a=str(f["f1_id"]).strip().lower();b=str(f["f2_id"]).strip().lower()
        except (ValueError,TypeError,KeyError):continue
        if not 0<duration<=1500 or not a or not b or a==b or len(day)!=10:continue
        fights.append((day,record["ufcstats_fight_id"],a,b,int(f["scheduled_rounds"]),duration))
    fights.sort()
    if len(fights)<10:raise ValueError("insufficient fights")
    cutoff=fights[int(len(fights)*train_fraction)][0]
    if cutoff==fights[0][0]:raise ValueError("no prior-date training")
    history=defaultdict(list);errors=defaultdict(list);excluded=defaultdict(int)
    for day in sorted({x[0] for x in fights}):
        batch=[x for x in fights if x[0]==day]
        for _,fid,a,b,fmt,actual in batch:
            if day<cutoff:continue
            own=history[a];opp=history[b]
            if len(own)<min_prior or len(opp)<min_prior:
                excluded["insufficient_prior_fights"]+=1;continue
            baseline=(sum(d for _,d in own)/len(own)+sum(d for _,d in opp)/len(opp))/2
            same_a=[d for r,d in own if r==fmt];same_b=[d for r,d in opp if r==fmt]
            if len(same_a)<min_prior or len(same_b)<min_prior:
                excluded["insufficient_same_format_history"]+=1;continue
            candidate=(sum(same_a)/len(same_a)+sum(same_b)/len(same_b))/2
            errors[str(fmt)].append((baseline,candidate,actual,fid))
        for _,fid,a,b,fmt,actual in batch:
            history[a].append((fmt,actual));history[b].append((fmt,actual))
    def summarize(items):
        n=len(items)
        if not n:return None
        base=sum(abs(x-y) for x,z,y,_ in items)/n
        candidate=sum(abs(z-y) for x,z,y,_ in items)/n
        return {"fights":n,"baseline_mae_seconds":base,"format_specific_mae_seconds":candidate,
                "mae_improvement_seconds":base-candidate,
                "baseline_rmse_seconds":math.sqrt(sum((x-y)**2 for x,z,y,_ in items)/n),
                "format_specific_rmse_seconds":math.sqrt(sum((z-y)**2 for x,z,y,_ in items)/n),
                "candidate_outperforms_baseline":candidate<base}
    all_items=[item for values in errors.values() for item in values]
    result=summarize(all_items)
    return {"schema":1,"holdout_start_date":cutoff,"total_eligible_fights":len(all_items),
      "paired_comparison":result,"by_scheduled_rounds":{k:summarize(v) for k,v in errors.items()},
      "excluded":dict(excluded),"duration_oracle":False,
      "scheduled_rounds_source_semantics_verified":False,"point_in_time_certified":False,
      "bet_eligible":False,"production_promotion_allowed":False,
      "limitations":"Research only. Scheduled-rounds field internally plausible but source semantics not independently verified. Same-format history requires three earlier bouts per fighter. No same-day history or holdout tuning. Only duration accuracy tested."}
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);args=p.parse_args()
    cross,_=fetch(BASE+"id_crosswalk_all.csv");wide,_=fetch(BASE+"ufc_all_fights_wide.csv")
    linked=join(cross,wide)
    if linked["status"]!="JOINED":raise SystemExit("fight join failed")
    report=evaluate(linked["records"])
    if not report["total_eligible_fights"]:raise SystemExit("no eligible holdout fights")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
