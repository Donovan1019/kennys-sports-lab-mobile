#!/usr/bin/env python3
"""Research-only chronological UFC probability of bout ending before 5 minutes.

An early finish is a duration outcome, not a verified method-of-victory label.
Same-day histories are isolated; no sportsbook or betting eligibility.
"""
import argparse,hashlib,json
from collections import defaultdict
from pathlib import Path
from scripts.ufc_native_fight_join import BASE,fetch,join

def evaluate(records,train_fraction=.8,min_prior=3,source_hashes=None):
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
    eligible_ids=sorted(fid for day,fid,a,b,duration in fights if day>=cutoff)
    holdout_fight_id_sha256=hashlib.sha256("\\n".join(eligible_ids).encode()).hexdigest()
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
            # Fixed 10-prior-fight pseudocount shrinkage; no holdout tuning.
            strength=10
            shrunk_a=(sum(history[a])+strength*baseline)/(len(history[a])+strength)
            shrunk_b=(sum(history[b])+strength*baseline)/(len(history[b])+strength)
            shrunk=(shrunk_a+shrunk_b)/2
            outcomes.append((baseline,candidate,actual,shrunk))
        for _,_,a,b,duration in batch:
            actual=int(duration<300)
            history[a].append(actual);history[b].append(actual);population.append(actual)
    n=len(outcomes)
    def metrics(index):
        if not n:return None
        return {"brier":sum((v[index]-v[2])**2 for v in outcomes)/n,
          "mean_predicted_probability":sum(v[index] for v in outcomes)/n,
          "observed_rate":sum(v[2] for v in outcomes)/n}
    def calibration(index):
        bins=[[] for _ in range(5)]
        for item in outcomes:
            probability=item[index]
            bins[min(4,int(probability*5))].append((probability,item[2]))
        return [{"probability_bin":i,"n":len(items),
          "mean_predicted_probability":sum(p for p,y in items)/len(items) if items else None,
          "observed_rate":sum(y for p,y in items)/len(items) if items else None}
          for i,items in enumerate(bins)]
    base=metrics(0);candidate=metrics(1);shrunk=metrics(3)
    return {"schema":1,"holdout_start_date":cutoff,"evaluated_fights":n,
      "target":"bout_duration_strictly_under_300_seconds",
      "source_sha256":source_hashes or {},"joined_eligible_fights":len(fights),
      "holdout_date_scoped_fights":len(eligible_ids),
      "holdout_fight_ids_sha256":holdout_fight_id_sha256,
      "split_fraction":train_fraction,"minimum_prior_fights":min_prior,
      "baseline_population_prior":base,"candidate_fighter_prior":candidate,
      "calibration_bins":{"population_prior":calibration(0),"fighter_prior":calibration(1),"shrunk_fighter_prior":calibration(3)},
      "calibration_bins_diagnostic_only":True,
      "candidate_shrunk_fighter_prior":shrunk,"shrinkage_pseudocount_fixed":10,
      "shrunk_brier_improvement":base["brier"]-shrunk["brier"] if n else None,
      "shrunk_decision":"REJECT" if not n or shrunk["brier"]>=base["brier"] else "RESEARCH_ONLY",
      "brier_improvement":base["brier"]-candidate["brier"] if n else None,
      "decision":"REJECT" if not n or candidate["brier"]>=base["brier"] else "RESEARCH_ONLY",
      "excluded":dict(excluded),"same_date_isolation":True,"candidate_weight_tuned_on_holdout":False,
      "point_in_time_certified":False,"calibrated":False,"bet_eligible":False,
      "production_promotion_allowed":False,
      "limitations":"Early-duration outcome is not independently verified finish method. Retrospective provenance not PIT certified; no confidence calibration, odds, or promotion."}
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);args=p.parse_args()
    cross,cross_hash=fetch(BASE+"id_crosswalk_all.csv");wide,wide_hash=fetch(BASE+"ufc_all_fights_wide.csv")
    linked=join(cross,wide)
    if linked["status"]!="JOINED":raise SystemExit("join failed")
    result=evaluate(linked["records"],source_hashes={"crosswalk":cross_hash,"wide":wide_hash})
    if not result["evaluated_fights"]:raise SystemExit("no holdout observations")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
