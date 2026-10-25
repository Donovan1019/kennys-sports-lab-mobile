#!/usr/bin/env python3
"""Research-only chronological UFC probability of bout ending before 5 minutes.

An early finish is a duration outcome, not a verified method-of-victory label.
Same-day histories are isolated; no sportsbook or betting eligibility.
"""
import argparse,json
from collections import defaultdict
from pathlib import Path
from scripts.ufc_native_fight_join import BASE,fetch,join

def evaluate(records,train_fraction=.8,min_prior=3):
    if not 0<train_fraction<1 or min_prior<1:raise ValueError("invalid parameters")
    fights=[]
    for record in records:
        f=record["wide_record"]
        try:
            day=str(f["event_date"])[:10];a=str(f["f1_id"]).strip().lower()
            b=str(f["f2_id"]).strip().lower();duration=float(f["fight_duration_sec"])
        except (ValueError,TypeError,KeyError):continue
        if not a or not b or a==b or not 0<duration<=1500 or len(day)!=10:continue
        fights.append((day,record["ufcstats_fight_id"],a,b,duration))
    fights.sort()
    if len(fights)<10:raise ValueError("insufficient fights")
    cutoff=fights[int(len(fights)*train_fraction)][0]
    if cutoff==fights[0][0]:raise ValueError("no training period")
    history=defaultdict(list);population=[];outcomes=[];excluded=defaultdict(int)
    for day in sorted({f[0] for f in fights}):
        batch=[f for f in fights if f[0]==day]
        for _,fid,a,b,duration in batch:
            if day<cutoff:continue
            if len(history[a])<min_prior or len(history[b])<min_prior or not population:
                excluded["insufficient_history"]+=1;continue
            # Fixed, unfitted candidate: average prior early-end rates of both fighters.
            candidate=(sum(history[a])/len(history[a])+sum(history[b])/len(history[b]))/2
            baseline=sum(population)/len(population)
            actual=int(duration<300)
            outcomes.append((baseline,candidate,actual))
        for _,_,a,b,duration in batch:
            actual=int(duration<300)
            history[a].append(actual);history[b].append(actual);population.append(actual)
    n=len(outcomes)
    def metrics(index):
        if not n:return None
        return {"brier":sum((v[index]-v[2])**2 for v in outcomes)/n,
          "mean_predicted_probability":sum(v[index] for v in outcomes)/n,
          "observed_rate":sum(v[2] for v in outcomes)/n}
    base=metrics(0);candidate=metrics(1)
    return {"schema":1,"holdout_start_date":cutoff,"evaluated_fights":n,
      "target":"bout_duration_strictly_under_300_seconds",
      "baseline_population_prior":base,"candidate_fighter_prior":candidate,
      "brier_improvement":base["brier"]-candidate["brier"] if n else None,
      "decision":"REJECT" if not n or candidate["brier"]>=base["brier"] else "RESEARCH_ONLY",
      "excluded":dict(excluded),"same_date_isolation":True,"candidate_weight_tuned_on_holdout":False,
      "point_in_time_certified":False,"calibrated":False,"bet_eligible":False,
      "production_promotion_allowed":False,
      "limitations":"Early-duration outcome is not independently verified finish method. Retrospective provenance not PIT certified; no confidence calibration, odds, or promotion."}
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);args=p.parse_args()
    cross,_=fetch(BASE+"id_crosswalk_all.csv");wide,_=fetch(BASE+"ufc_all_fights_wide.csv")
    linked=join(cross,wide)
    if linked["status"]!="JOINED":raise SystemExit("join failed")
    result=evaluate(linked["records"])
    if not result["evaluated_fights"]:raise SystemExit("no holdout observations")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
