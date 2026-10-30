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
            all_forecasts.append({'fight_id':fid,'event_id':eid,'start_time':t.isoformat(),'winner_probability':probability,'winner_prior_bouts':bouts.get(winner,0),'loser_prior_bouts':bouts.get(loser,0)})
            if bouts.get(winner,0)>=minimum_history and bouts.get(loser,0)>=minimum_history:
                forecasts.append({'fight_id':fid,'event_id':eid,'start_time':t.isoformat(),
                                  'winner':winner,'loser':loser,'winner_probability':probability,
                                  'model_version':'ufc-elo-baseline-v1','research_only':True,'bet_eligible':False})
            updates.append((winner,loser,rw,rl,k*(1-probability)))
        for winner,loser,rw,rl,delta in updates:
            ratings[winner]=rw+delta
            ratings[loser]=rl-delta
            bouts[winner]=bouts.get(winner,0)+1
            bouts[loser]=bouts.get(loser,0)+1
    # Time-ordered holdout on the strict minimum-history cohort.
    # Do not fit Elo hyperparameters on the holdout window.
    cutoff=int(len(forecasts)*0.8)
    holdout=forecasts[cutoff:] if cutoff else []
    holdout_brier=sum((1-x['winner_probability'])**2 for x in holdout)/len(holdout) if holdout else None
    holdout_log_loss=sum(-math.log(max(1e-12,x['winner_probability'])) for x in holdout)/len(holdout) if holdout else None
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
            "holdout_evaluated_fights":len(holdout),"holdout_start":holdout_start,"holdout_end":holdout_end,"holdout_brier":holdout_brier,"holdout_log_loss":holdout_log_loss,"holdout_brier_skill_vs_50pct":holdout_skill,"holdout_status":"INSUFFICIENT_SAMPLE" if len(holdout)<30 else "CHRONOLOGICAL_EVALUATION_ONLY","all_pre_update_forecasts":all_forecasts,"ratings":{name:{"elo":round(ratings[name],2),"historical_bouts":bouts[name]}
                       for name in sorted(ratings)},"forecasts":forecasts,
            "bet_eligible":False,"calibration_status":"INSUFFICIENT_SAMPLE" if n<100 else "REQUIRES_INDEPENDENT_HOLDOUT",
            "limitations":["Same-event predictions use a frozen pre-event rating snapshot",
                           "No fighter inactivity, age, weight class, injuries, or style adjustments",
                           "Chronological holdout is descriptive only; no independent external validation or archived odds"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",default="backtests/reports/ufc_elo_baseline.json")
    args=p.parse_args()
    raw=Path(args.input).read_bytes()
    rows=json.loads(raw)["results"]
    report=build(rows)
    report["input_sha256"]=hashlib.sha256(raw).hexdigest()
    report["input_path"]=str(args.input)
    output=Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+"\n")
    print(f"UFC Elo: {report['historical_bouts_used']} historical bouts, {report['pre_update_evaluated_fights']} pre-update evaluations")
if __name__=="__main__":
    main()
