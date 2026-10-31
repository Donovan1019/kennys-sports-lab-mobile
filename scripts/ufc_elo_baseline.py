#!/usr/bin/env python3
"""Chronological UFC Elo baseline: opponent-adjusted winner predictions.
Research only until verified data coverage, holdout calibration and sportsbook lines.
"""
import argparse
import datetime as dt
import json
import math
import hashlib
from pathlib import Path

def parse_time(value):
    t=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    if t.tzinfo is None:
        raise ValueError("Timezone required")
    return t.astimezone(dt.timezone.utc)

def build(rows,k=24,minimum_history=5):
    if not isinstance(rows,list):
        raise ValueError("Historical results must be a list")
    if not 0<k<=100 or not isinstance(minimum_history,int) or minimum_history<1:
        raise ValueError("Invalid Elo parameters")
    eligible=[]
    for row in rows:
        if not isinstance(row,dict) or row.get("winner_verified") is not True:
            continue
        try:
            winner,loser=row["winner"].strip(),row["loser"].strip()
            event_id,fight_id=row["event_id"],row["fight_id"]
            t=parse_time(row["event_date"])
            if not winner or not loser or winner==loser or not event_id or not fight_id:
                continue
        except (KeyError,ValueError,TypeError,AttributeError):
            continue
        eligible.append((t,str(event_id),str(fight_id),winner,loser))
    eligible.sort()
    # Reject ambiguous chronology: an event must not contain conflicting dates.
    event_dates={}
    for t,eid,fid,winner,loser in eligible:
        event_dates.setdefault(eid,set()).add(t.date())
    ambiguous_events={eid for eid,dates in event_dates.items() if len(dates)>1}
    eligible=[row for row in eligible if row[1] not in ambiguous_events]
    ratings={}
    bouts={}
    last_fight={}
    seen=set()
    forecasts=[]
    all_forecasts=[]
    # Evaluate every bout against the pre-event rating snapshot, not outcomes
    # from another fight on the same card. Only then apply all event updates.
    event_groups={}
    for item in eligible:
        event_groups.setdefault(item[1],[]).append(item)
    for event_id,group in sorted(event_groups.items(),key=lambda pair:(min(x[0] for x in pair[1]),pair[0])):
        updates=[]
        for t,eid,fid,winner,loser in group:
            key=(eid,fid)
            if key in seen:
                continue
            seen.add(key)
            rw=ratings.get(winner,1500.0)
            rl=ratings.get(loser,1500.0)
            probability=1/(1+10**((rl-rw)/400))
            winner_days=(t-last_fight[winner]).days if winner in last_fight else None
            loser_days=(t-last_fight[loser]).days if loser in last_fight else None
            all_forecasts.append({'fight_id':fid,'event_id':eid,'start_time':t.isoformat(),'winner_probability':probability,'winner_prior_bouts':bouts.get(winner,0),'loser_prior_bouts':bouts.get(loser,0),'winner_days_since_last_fight':winner_days,'loser_days_since_last_fight':loser_days})
            if bouts.get(winner,0)>=minimum_history and bouts.get(loser,0)>=minimum_history:
                forecasts.append({'fight_id':fid,'event_id':eid,'start_time':t.isoformat(),
                                  'winner':winner,'loser':loser,'winner_probability':probability,'inactivity_gap_days':(winner_days-loser_days) if winner_days is not None and loser_days is not None else None,
                                  'model_version':'ufc-elo-baseline-v1','research_only':True,'bet_eligible':False})
            updates.append((winner,loser,rw,rl,k*(1-probability)))
        for winner,loser,rw,rl,delta in updates:
            ratings[winner]=rw+delta
            ratings[loser]=rl-delta
            bouts[winner]=bouts.get(winner,0)+1
            bouts[loser]=bouts.get(loser,0)+1
            last_fight[winner]=group[0][0]
            last_fight[loser]=group[0][0]
    # Time-ordered holdout on the strict minimum-history cohort.
    # Do not fit Elo hyperparameters on the holdout window.
    cutoff=int(len(forecasts)*0.8)
    holdout=forecasts[cutoff:] if cutoff else []
    holdout_brier=sum((1-x['winner_probability'])**2 for x in holdout)/len(holdout) if holdout else None
    holdout_log_loss=sum(-math.log(max(1e-12,x['winner_probability'])) for x in holdout)/len(holdout) if holdout else None
    # Fit a single probability-shrinkage parameter on the earlier 80% only.
    # This is an exploratory walk-forward calibration check, not sportsbook validation.
    train=forecasts[:cutoff]
    shrinkages=(0.0,0.25,0.5,0.75,1.0)
    def adjusted(p,weight):
        return 0.5+weight*(p-0.5)
    def score(items,weight):
        return sum(-math.log(max(1e-12,adjusted(x["winner_probability"],weight))) for x in items)/len(items) if items else None
    chosen=min(shrinkages,key=lambda weight:(score(train,weight),weight)) if train else None
    calibrated_brier=(sum((1-adjusted(x["winner_probability"],chosen))**2 for x in holdout)/len(holdout)) if holdout and chosen is not None else None
    calibrated_log_loss=score(holdout,chosen) if chosen is not None else None
    calibration_audit={"status":"RESEARCH_ONLY","fit_count":len(train),"holdout_count":len(holdout),
        "fit_only_on_pre_holdout":True,"candidate_shrinkages":list(shrinkages),
        "selected_shrinkage":chosen,"holdout_brier":calibrated_brier,
        "holdout_log_loss":calibrated_log_loss,
        "delta_brier_vs_raw":(calibrated_brier-holdout_brier) if calibrated_brier is not None else None,
        "delta_log_loss_vs_raw":(calibrated_log_loss-holdout_log_loss) if calibrated_log_loss is not None else None}
    # Train inactivity adjustment on the earlier cohort only; never tune on holdout.
    # The gap is signed relative to the actual winner, with a symmetric
    # pre-fight logit adjustment. Keep the baseline untouched.
    def inactivity_prob(item,coefficient):
        p=min(1-1e-12,max(1e-12,item["winner_probability"]))
        gap=item.get("inactivity_gap_days")
        if gap is None:
            return p
        gap=max(-365,min(365,gap))/365.0
        logit=math.log(p/(1-p))-coefficient*gap
        return 1/(1+math.exp(-logit))
    def inactivity_metrics(items,coefficient):
        if not items:
            return {"count":0,"brier":None,"log_loss":None}
        probabilities=[inactivity_prob(x,coefficient) for x in items]
        return {"count":len(items),
                "brier":sum((1-p)**2 for p in probabilities)/len(items),
                "log_loss":sum(-math.log(max(1e-12,p)) for p in probabilities)/len(items)}
    inactivity_candidates=(-1.0,-0.5,-0.25,0.0,0.25,0.5,1.0)
    usable_train=[x for x in train if x.get("inactivity_gap_days") is not None]
    usable_holdout=[x for x in holdout if x.get("inactivity_gap_days") is not None]
    selected_inactivity=(min(inactivity_candidates,
        key=lambda c:(inactivity_metrics(usable_train,c)["log_loss"],abs(c),c))
        if len(usable_train)>=30 else 0.0)
    inactivity_raw=inactivity_metrics(holdout,0.0)
    inactivity_adjusted=inactivity_metrics(holdout,selected_inactivity)
    inactivity_audit={"status":"RESEARCH_ONLY","train_available":len(usable_train),
        "holdout_available":len(usable_holdout),"holdout_total":len(holdout),
        "candidate_coefficients":list(inactivity_candidates),
        "selected_coefficient":selected_inactivity,"fit_only_on_pre_holdout":True,
        "raw_holdout":inactivity_raw,"adjusted_holdout":inactivity_adjusted,
        "delta_brier":inactivity_adjusted["brier"]-inactivity_raw["brier"] if holdout else None,
        "delta_log_loss":inactivity_adjusted["log_loss"]-inactivity_raw["log_loss"] if holdout else None,
        "deployed_to_live_predictions":False}
    # Expanding-window evaluation: each fold trains only on earlier fights.
    # No overlapping evaluation windows, and no coefficient tuned on test fights.
    window_audit=[]
    for train_fraction,test_fraction in ((0.5,0.1),(0.6,0.1),(0.7,0.1),(0.8,0.2)):
        start=int(len(forecasts)*train_fraction)
        end=min(len(forecasts),int(len(forecasts)*(train_fraction+test_fraction)))
        past=[x for x in forecasts[:start] if x.get("inactivity_gap_days") is not None]
        future=forecasts[start:end]
        if len(past)<30 or len(future)<30:
            continue
        coefficient=min(inactivity_candidates,
            key=lambda c:(inactivity_metrics(past,c)["log_loss"],abs(c),c))
        raw=inactivity_metrics(future,0.0)
        adjusted_window=inactivity_metrics(future,coefficient)
        window_audit.append({"train_count":start,"test_count":len(future),
            "start_time":future[0]["start_time"],"end_time":future[-1]["start_time"],
            "selected_coefficient":coefficient,"raw_brier":raw["brier"],
            "adjusted_brier":adjusted_window["brier"],
            "delta_brier":adjusted_window["brier"]-raw["brier"],
            "raw_log_loss":raw["log_loss"],"adjusted_log_loss":adjusted_window["log_loss"],
            "delta_log_loss":adjusted_window["log_loss"]-raw["log_loss"]})
    inactivity_walk_forward={"status":"RESEARCH_ONLY",
        "method":"expanding_train_disjoint_test_windows",
        "windows":window_audit,"deployed_to_live_predictions":False}
    # Source contract: the imported fight-results feed contains winners and
    # dates, not verified per-fighter striking/takedown statistics. Never
    # fabricate these fields or fit a challenger on unavailable measurements.
    feature_readiness={"status":"BLOCKED_MISSING_VERIFIED_FIGHT_STATS",
        "source":"Greco1899 UFCStats event/results CSVs",
        "available":["historical_outcomes","prior_opponent_elo","prior_bout_count","inactivity_days"],
        "unavailable":["pre_fight_significant_strikes","pre_fight_takedowns",
                       "pre_fight_control_time","pre_fight_weight_class"],
        "striking_challenger_evaluated":False,
        "grappling_challenger_evaluated":False,
        "live_predictions_modified":False,
        "reason":"Results-only import has no timestamped per-fighter fight statistics"}
    holdout_skill=(1-holdout_brier/0.25) if holdout else None
    # 50% is a diagnostic reference; compare against chronological pre-fight
    # sportsbook probabilities separately when licensed historical odds exist.
    holdout_start=holdout[0]['start_time'] if holdout else None
    holdout_end=holdout[-1]['start_time'] if holdout else None
    n=len(forecasts)
    all_n=len(all_forecasts)
    all_brier=sum((1-x['winner_probability'])**2 for x in all_forecasts)/all_n if all_n else None
    all_log_loss=sum(-math.log(max(1e-12,x['winner_probability'])) for x in all_forecasts)/all_n if all_n else None
    baseline_brier=0.25 if n else None
    baseline_log_loss=math.log(2) if n else None
    brier=sum((1-x["winner_probability"])**2 for x in forecasts)/n if n else None
    loss=sum(-math.log(x["winner_probability"]) for x in forecasts)/n if n else None
    improvement_brier=(baseline_brier-brier)/baseline_brier if n else None
    return {"schema":1,"sport":"UFC","model_version":"ufc-elo-baseline-v1",
            "historical_bouts_used":len(seen),"excluded_ambiguous_date_events":len(ambiguous_events),"pre_update_evaluated_fights":n,"all_pre_update_evaluated_fights":all_n,"all_pre_update_brier":all_brier,"all_pre_update_log_loss":all_log_loss,"all_pre_update_brier_skill_vs_50pct":(1-all_brier/0.25) if all_n else None,
            "brier":brier,"log_loss":loss,"baseline_brier":baseline_brier,"baseline_log_loss":baseline_log_loss,"brier_skill_vs_50pct":improvement_brier,"minimum_prior_bouts_per_fighter":minimum_history,
            "holdout_evaluated_fights":len(holdout),"calibration_audit":calibration_audit,"inactivity_audit":inactivity_audit,"inactivity_walk_forward":inactivity_walk_forward,"fighter_feature_readiness":feature_readiness,"holdout_start":holdout_start,"holdout_end":holdout_end,"holdout_brier":holdout_brier,"holdout_log_loss":holdout_log_loss,"holdout_brier_skill_vs_50pct":holdout_skill,"holdout_status":"INSUFFICIENT_SAMPLE" if len(holdout)<30 else "CHRONOLOGICAL_EVALUATION_ONLY","all_pre_update_forecasts":all_forecasts,"ratings":{name:{"elo":round(ratings[name],2),"historical_bouts":bouts[name]}
                       for name in sorted(ratings)},"forecasts":forecasts,
            "bet_eligible":False,"calibration_status":"INSUFFICIENT_SAMPLE" if n<100 else "REQUIRES_INDEPENDENT_HOLDOUT",
            "limitations":["Same-event predictions use a frozen pre-event rating snapshot",
                           "Inactivity adjustment evaluated as research only; no age, weight class, injuries, or style adjustments in live predictions",
                           "Chronological holdout is descriptive only; no independent external validation or archived odds"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--minimum-evaluated",type=int,default=0,help="Minimum strict pre-event evaluations required")
    p.add_argument("--output",default="backtests/reports/ufc_elo_baseline.json")
    args=p.parse_args()
    raw=Path(args.input).read_bytes()
    payload=json.loads(raw)
    if not isinstance(payload,dict) or not isinstance(payload.get("results"),list):
        raise ValueError("Historical input must contain a results list")
    rows=payload["results"]
    report=build(rows)
    report["input_sha256"]=hashlib.sha256(raw).hexdigest()
    report["input_path"]=str(args.input)
    report["input_record_count"]=len(rows)
    report["input_verified_winner_count"]=sum(isinstance(row,dict) and row.get("winner_verified") is True for row in rows)
    report["input_rejected_count"]=len(rows)-report["historical_bouts_used"]
    if args.minimum_evaluated < 0:
        raise ValueError("--minimum-evaluated must be nonnegative")
    if report["pre_update_evaluated_fights"] < args.minimum_evaluated:
        raise SystemExit("UFC coverage gate failed: {} evaluated, {} required".format(
            report["pre_update_evaluated_fights"],args.minimum_evaluated))
    output=Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+"\n")
    print(f"UFC Elo: {report['historical_bouts_used']} historical bouts, {report['pre_update_evaluated_fights']} pre-update evaluations")
if __name__=="__main__":
    main()
