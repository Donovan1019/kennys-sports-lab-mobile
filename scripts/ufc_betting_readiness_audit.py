#!/usr/bin/env python3
"""Matched-fight Elo comparison and conservative sportsbook readiness gate.

Research only: never convert unverified historical odds into bet recommendations.
"""
import argparse
import datetime as dt
import json
import math
from collections import defaultdict
from pathlib import Path

def forecasts(snapshot, k, min_bouts=8):
    if snapshot.get("bet_eligible") is not False or snapshot.get("snapshot")!="2026-07-07":
        raise ValueError("Historical research snapshot required")
    by_day=defaultdict(list)
    seen=set()
    for r in snapshot.get("fight_history",{}).get("rows",[]):
        if not isinstance(r,dict) or r.get("independently_verified") is not False:
            continue
        try:
            day=dt.date.fromisoformat(r["event_date"])
            key=r["source_fight_url"]
            w,l=r["winner"],r["loser"]
        except (KeyError,ValueError,TypeError):
            continue
        if not key or key in seen or not w or not l or w==l:
            continue
        seen.add(key)
        by_day[day].append((key,w,l))
    ratings,bouts={},{}
    result={}
    for day in sorted(by_day):
        changes=defaultdict(float)
        increments=defaultdict(int)
        for key,w,l in by_day[day]:
            p=1/(1+10**((ratings.get(l,1500)-ratings.get(w,1500))/400))
            if bouts.get(w,0)>=min_bouts and bouts.get(l,0)>=min_bouts:
                result[key]={"date":day.isoformat(),"winner_probability":p}
            d=k*(1-p)
            changes[w]+=d
            changes[l]-=d
            increments[w]+=1
            increments[l]+=1
        for name,d in changes.items():
            ratings[name]=ratings.get(name,1500)+d
            bouts[name]=bouts.get(name,0)+increments[name]
    return result

def metrics(ps):
    n=len(ps)
    return {"n":n,"brier":sum((1-p)**2 for p in ps)/n if n else None,
            "log_loss":sum(-math.log(max(p,1e-12)) for p in ps)/n if n else None}

def audit(snapshot, start="2023-03-18"):
    old=forecasts(snapshot,24,8)
    new=forecasts(snapshot,48,8)
    keys=sorted(k for k in old.keys() & new.keys() if old[k]["date"]>=start and new[k]["date"]>=start)
    baseline=metrics([old[k]["winner_probability"] for k in keys])
    tuned=metrics([new[k]["winner_probability"] for k in keys])
    return {"schema":1,"sport":"UFC","method":"matched_fight_holdout_comparison",
            "holdout_start":start,"min_prior_bouts":8,"matched_fights":len(keys),
            "original_k24":baseline,"tuned_k48":tuned,
            "brier_gain":baseline["brier"]-tuned["brier"] if keys else None,
            "log_loss_gain":baseline["log_loss"]-tuned["log_loss"] if keys else None,
            "tuned_better_on_both":bool(keys and tuned["brier"]<baseline["brier"] and tuned["log_loss"]<baseline["log_loss"]),
            "bet_eligible":False,"readiness":{"timestamped_bookmaker_odds":False,
                "independent_fight_verification":False,"prospective_calibration":False,
                "fighter_status_verified":False,"profitable_after_vig":False},
            "limitations":["Matched historical results are not independently verified",
                "Previously inspected holdout, not a pristine prospective test",
                "No market EV or betting recommendations without timestamped executable odds"]}

def decimal_odds(american):
    if type(american) not in (int,float) or not math.isfinite(american) or -100<american<100:
        raise ValueError("Invalid American odds")
    return 1+american/100 if american>0 else 1+100/abs(american)

def quote_gate(quote):
    required=("market","selection","american_odds","observed_at_utc","event_start_utc",
              "sportsbook","fighter_status_verified","independent_source_verified")
    if any(x not in quote for x in required):
        return {"eligible":False,"reason":"MISSING_REQUIRED_FIELDS"}
    if quote["fighter_status_verified"] is not True or quote["independent_source_verified"] is not True:
        return {"eligible":False,"reason":"UNVERIFIED_INPUTS"}
    try:
        observed=dt.datetime.fromisoformat(quote["observed_at_utc"].replace("Z","+00:00"))
        event=dt.datetime.fromisoformat(quote["event_start_utc"].replace("Z","+00:00"))
        if observed.utcoffset() is None or event.utcoffset() is None or observed>=event:
            return {"eligible":False,"reason":"INVALID_ODDS_TIMING"}
        decimal_odds(quote["american_odds"])
    except (ValueError,TypeError,AttributeError):
        return {"eligible":False,"reason":"INVALID_ODDS_OR_TIMESTAMP"}
    return {"eligible":False,"reason":"MODEL_NOT_PROSPECTIVELY_CALIBRATED"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    result=audit(json.loads(Path(args.input).read_text()))
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print("Matched holdout fights:",result["matched_fights"])
    print("Original K24 Brier:",result["original_k24"]["brier"])
    print("Tuned K48 Brier:",result["tuned_k48"]["brier"])
    print("Matched Brier gain:",result["brier_gain"])
    print("Tuned better on both:",result["tuned_better_on_both"])
    print("Bet eligible:",result["bet_eligible"])

if __name__=="__main__":
    main()
