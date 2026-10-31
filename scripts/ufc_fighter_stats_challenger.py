#!/usr/bin/env python3
"""Chronological UFC fighter-stat challenger; research only, no live promotion."""
import argparse
import json
import math
from pathlib import Path

def evaluate(elo,features):
    lookup={x["fight_id"]:x for x in features["features"]}
    rows=[]
    for forecast in elo["forecasts"]:
        record=lookup.get(forecast["fight_id"])
        if not record or record["winner"]!=forecast["winner"] or record["loser"]!=forecast["loser"]:
            continue
        a=record["pre_fight"][forecast["winner"]]
        b=record["pre_fight"][forecast["loser"]]
        if min(a["prior_fights"],b["prior_fights"])<5:
            continue
        if any(a[k] is None or b[k] is None for k in ("prior_sig_strikes_per_recorded_round","prior_takedowns_per_recorded_round")):
            continue
        p=forecast["winner_probability"]
        if not 0<p<1:
            continue
        ds=max(-3,min(3,(a["prior_sig_strikes_per_recorded_round"]-b["prior_sig_strikes_per_recorded_round"])/10))
        dt=max(-3,min(3,(a["prior_takedowns_per_recorded_round"]-b["prior_takedowns_per_recorded_round"])/1))
        rows.append((forecast["start_time"],forecast["fight_id"],p,ds,dt))
    rows.sort(key=lambda x:(x[0],x[1]))
    # Use Elo's original chronological holdout boundary; never redefine the holdout to
    # make a better-looking challenger sample.
    holdout_start=elo["holdout_start"]
    train=[r for r in rows if r[0]<holdout_start]
    test=[r for r in rows if r[0]>=holdout_start]
    def probability(r,cs,ct):
        _,_,p,ds,dt=r
        logit=math.log(p/(1-p))+cs*ds+ct*dt
        return 1/(1+math.exp(-max(-30,min(30,logit))))
    def metrics(items,cs,ct):
        if not items:
            return {"count":0,"brier":None,"log_loss":None}
        ps=[probability(r,cs,ct) for r in items]
        return {"count":len(ps),"brier":sum((1-p)**2 for p in ps)/len(ps),
                "log_loss":sum(-math.log(max(1e-12,p)) for p in ps)/len(ps)}
    candidates=(-1.0,-0.8,-0.6,-0.4,-0.2,0.0,0.2,0.4,0.6,0.8,1.0)
    # All observed rows are oriented toward the winner, but a signed difference
    # is antisymmetric: the equivalent loser-oriented sample has y=0 and 1-p.
    # This yields exactly the same proper scoring loss without doubling rows.
    if len(train)<100 or len(test)<30:
        return {"status":"INSUFFICIENT_COHORT","train_count":len(train),"holdout_count":len(test),
                "deployed_to_live_predictions":False}
    selected=min(((cs,ct) for cs in candidates for ct in candidates),
                 key=lambda pair:(metrics(train,*pair)["log_loss"],abs(pair[0])+abs(pair[1]),pair))
    # Expanding chronological windows with non-overlapping test intervals.
    # Entire timestamp groups remain in one fold to avoid same-event leakage.
    folds=[]
    for train_fraction,end_fraction in ((0.5,0.6),(0.6,0.7),(0.7,0.8),(0.8,1.0)):
        start_index=int(len(rows)*train_fraction)
        end_index=int(len(rows)*end_fraction)
        if start_index>=len(rows):
            continue
        start_time=rows[start_index][0]
        end_time=rows[end_index][0] if end_index<len(rows) else None
        past=[r for r in rows if r[0]<start_time]
        future=[r for r in rows if r[0]>=start_time and (end_time is None or r[0]<end_time)]
        if len(past)<100 or len(future)<30:
            continue
        coeff=min(((cs,ct) for cs in candidates for ct in candidates),
                  key=lambda pair:(metrics(past,*pair)["log_loss"],abs(pair[0])+abs(pair[1]),pair))
        raw=metrics(future,0,0)
        adjusted=metrics(future,*coeff)
        folds.append({"train_count":len(past),"test_count":len(future),
                      "start_time":start_time,"end_time":future[-1][0],
                      "sig_coefficient":coeff[0],"td_coefficient":coeff[1],
                      "elo_brier":raw["brier"],"challenger_brier":adjusted["brier"],
                      "delta_brier":adjusted["brier"]-raw["brier"],
                      "elo_log_loss":raw["log_loss"],"challenger_log_loss":adjusted["log_loss"],
                      "delta_log_loss":adjusted["log_loss"]-raw["log_loss"]})
    walk_forward={"status":"RESEARCH_ONLY","method":"expanding_train_disjoint_date_grouped_test",
                  "windows":folds,"brier_improved_windows":sum(w["delta_brier"]<0 for w in folds),
                  "log_loss_improved_windows":sum(w["delta_log_loss"]<0 for w in folds),
                  "coefficient_grid_boundary":1.0,
                  "boundary_selected_windows":sum(abs(w["sig_coefficient"])==1.0 or abs(w["td_coefficient"])==1.0 for w in folds),
                  "live_predictions_updated":False}
    # Paired date-cluster bootstrap; preserve dependence among fights on one card.
    import random
    rng=random.Random(16016)
    grouped={}
    for row in test:
        grouped.setdefault(row[0][:10],[]).append(row)
    dates=sorted(grouped)
    deltas_brier=[]
    deltas_loss=[]
    if len(dates)>=20:
        for _ in range(500):
            sample=[row for date in rng.choices(dates,k=len(dates)) for row in grouped[date]]
            base=metrics(sample,0,0)
            changed=metrics(sample,*selected)
            deltas_brier.append(changed["brier"]-base["brier"])
            deltas_loss.append(changed["log_loss"]-base["log_loss"])
    def interval(values):
        if not values:
            return None
        values.sort()
        return [values[int(.025*(len(values)-1))],values[int(.975*(len(values)-1))]]
    uncertainty={"method":"paired_date_cluster_bootstrap","replicates":len(deltas_brier),
                 "delta_brier_95pct_interval":interval(deltas_brier),
                 "delta_log_loss_95pct_interval":interval(deltas_loss)}
    # Winner-oriented probabilities have target 1.0; audit bins are descriptive,
    # not calibration fitting. No holdout values influence coefficients.
    def reliability_bins(items,cs,ct):
        bins=[]
        for low,high in ((0.0,0.2),(0.2,0.4),(0.4,0.6),(0.6,0.8),(0.8,1.0)):
            ps=[probability(r,cs,ct) for r in items if low<=probability(r,cs,ct)<high or (high==1.0 and probability(r,cs,ct)==1.0)]
            bins.append({"range":[low,high],"count":len(ps),
                         "mean_predicted_winner_probability":sum(ps)/len(ps) if ps else None,
                         "observed_winner_rate":1.0 if ps else None})
        return bins
    # Confidence strata defined by the unchanged Elo probability, ensuring
    # baseline and challenger are compared on exactly the same fight subsets.
    strata=[]
    for low,high in ((0.0,0.4),(0.4,0.5),(0.5,0.6),(0.6,0.7),(0.7,1.0)):
        subset=[r for r in test if low<=r[2]<high or (high==1.0 and r[2]==1.0)]
        base=metrics(subset,0,0)
        changed=metrics(subset,*selected)
        strata.append({"elo_probability_range":[low,high],"count":len(subset),
                       "elo":base,"challenger":changed,
                       "delta_brier":changed["brier"]-base["brier"] if subset else None,
                       "delta_log_loss":changed["log_loss"]-base["log_loss"] if subset else None})
    calibration_audit={"status":"DESCRIPTIVE_HOLDOUT_ONLY",
                       "target_orientation":"winner_probability_y_equals_one",
                       "elo_bins":reliability_bins(test,0,0),
                       "challenger_bins":reliability_bins(test,*selected),
                       "fixed_elo_confidence_strata":strata,
                       "calibration_fitted_on_holdout":False}
    baseline=metrics(test,0,0)
    challenger=metrics(test,*selected)
    return {"status":"RESEARCH_ONLY_NOT_BET_ELIGIBLE",
            "train_count":len(train),"holdout_count":len(test),
            "original_elo_holdout_start":holdout_start,
            "selection":"train_log_loss_only_grid_search",
            "selected_sig_coefficient":selected[0],"selected_td_coefficient":selected[1],
            "walk_forward":walk_forward,"uncertainty":uncertainty,"calibration_audit":calibration_audit,"matched_cohort_elo":baseline,"matched_cohort_challenger":challenger,
            "delta_brier":challenger["brier"]-baseline["brier"],
            "delta_log_loss":challenger["log_loss"]-baseline["log_loss"],
            "promotion_gate":{"status":"BLOCKED_INDEPENDENT_MARKET_VALIDATION","approved_for_live_predictions":False},"independent_market_validation":False,"deployed_to_live_predictions":False,
            "limitations":["Post-fight mirror stats are used only through prior-dated aggregates",
                           "Matched cohort comparison is not the full 501-fight Elo holdout",
                           "No independent sportsbook odds validation or betting certification"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--elo",required=True)
    p.add_argument("--features",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    report=evaluate(json.loads(Path(args.elo).read_text()),json.loads(Path(args.features).read_text()))
    Path(args.output).write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))
if __name__=="__main__":
    main()
