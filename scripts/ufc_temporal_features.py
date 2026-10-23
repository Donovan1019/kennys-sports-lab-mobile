#!/usr/bin/env python3
"""Leakage-safe UFC temporal, opponent-quality and uncertainty diagnostics.
Research features only; coefficients must be learned on historical training data.
"""
import argparse
import datetime as dt
import json
import math
from collections import defaultdict
from pathlib import Path

def instant(value):
    x=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    if x.tzinfo is None:
        raise ValueError("Timezone-aware timestamps required")
    return x.astimezone(dt.timezone.utc)

def features(rows,as_of,half_life_days=365,prior_strength=5):
    cutoff=instant(as_of)
    if not 0<half_life_days<=3650 or not 0<prior_strength<=100:
        raise ValueError("Invalid feature hyperparameters")
    if not isinstance(rows,list):
        raise ValueError("Expected list of completed fights")
    valid=[]
    seen=set()
    for r in rows:
        if not isinstance(r,dict) or r.get("winner_verified") is not True:
            continue
        try:
            t=instant(r["event_date"])
            eid,fid=str(r["event_id"]),str(r["fight_id"])
            winner,loser=r["winner"],r["loser"]
            if not eid or not fid or not winner or not loser or winner==loser or t>=cutoff:
                continue
        except (KeyError,ValueError,TypeError,AttributeError):
            continue
        key=(eid,fid)
        if key in seen:continue
        seen.add(key)
        valid.append((t,winner,loser))
    valid.sort(key=lambda x:x[0])
    records=defaultdict(list)
    for t,w,l in valid:
        records[w].append((t,1,l))
        records[l].append((t,0,w))
    # Opponent prior win rates are computed at each historical bout's timestamp,
    # excluding the target bout and later outcomes.
    past=defaultdict(lambda:[0,0])
    opponent_at_bout={}
    for t,w,l in valid:
        opponent_at_bout[(t,w,l)]=(past[l][0]+prior_strength*.5)/(past[l][1]+prior_strength)
        opponent_at_bout[(t,l,w)]=(past[w][0]+prior_strength*.5)/(past[w][1]+prior_strength)
        past[w][0]+=1;past[w][1]+=1
        past[l][1]+=1
    output=[]
    for fighter,history in sorted(records.items()):
        history.sort(key=lambda x:x[0])
        weights=[2**(-(cutoff-t).total_seconds()/86400/half_life_days) for t,_,_ in history]
        effective=sum(weights)
        weighted_wins=sum(weight*won for weight,(_,won,_) in zip(weights,history))
        smoothed=(weighted_wins+prior_strength*.5)/(effective+prior_strength)
        n=len(history)
        uncertainty=math.sqrt(smoothed*(1-smoothed)/(effective+prior_strength+1))
        opposition=sum(weight*opponent_at_bout[(t,fighter,opponent)] for weight,(t,_,opponent) in zip(weights,history))/effective if effective else None
        last=history[-1][0]
        days_since=(cutoff-last).total_seconds()/86400
        output.append({"fighter":fighter,"historical_bouts":n,"effective_recency_weighted_bouts":round(effective,3),
                       "recency_smoothed_win_rate":round(smoothed,4),
                       "approx_uncertainty_sd":round(uncertainty,4),
                       "historical_opponent_prior_win_rate":round(opposition,4) if opposition is not None else None,
                       "days_since_last_fight":round(days_since,1),
                       "low_sample_warning":effective<5,
                       "inactivity_warning":days_since>540})
    return {"schema":1,"as_of":cutoff.isoformat(),"fighters":output,"research_only":True,
            "bet_eligible":False,"model_probabilities":False,
            "limitations":["Opponent-quality estimate uses prior historical win rates, not fully adjusted skill",
                           "Smoothed win rate and uncertainty are descriptive, not calibrated win probabilities",
                           "Weight-class, age, injuries, and short-notice effects require verified inputs",
                           "Same-timestamp fight order is uncertain; use event-level ordering safeguards"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--as-of",required=True)
    p.add_argument("--output",default="backtests/reports/ufc_temporal_features.json")
    a=p.parse_args()
    result=features(json.loads(Path(a.input).read_text())["results"],a.as_of)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print("UFC temporal feature rows",len(result["fighters"]))
if __name__=="__main__":main()
