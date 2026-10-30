#!/usr/bin/env python3
"""Deterministic NBA ML Monte Carlo audit. Diagnostics only; no betting certification."""
import datetime as dt
import hashlib
import json
import math
import pathlib
import random

def decimal(price):
    return 1 + (100 / -price if price < 0 else price / 100)

def build(odds, model, readiness, now, draws=10000):
    report={"status":"unavailable","generated_at":now.isoformat(),"draws":draws,"games":[],"parlays":[],"betting_eligible":False,"blockers":[]}
    required=("odds_fresh","model_fresh_and_calibrated","schedule_evidence_fresh","pregame_odds_archiving_active","historical_pregame_odds_backtest","closing_line_value_verified","injury_lineup_rest_confirmed","executable_same_book_parlay_quote","correlation_stress_test_verified")
    report["blockers"]=[key for key in required if readiness.get("checks",{}).get(key) is not True]
    if model.get("status")!="validated" or model.get("calibration_passed") is not True or odds.get("status")!="ok":
        report["blockers"].append("validated_model_or_odds_missing")
        return report
    try:
        for obj,key in ((model,"generated_at"),(odds,"fetched_at")):
            stamp=dt.datetime.fromisoformat(obj[key].replace("Z","+00:00"))
            if not 0<=(now-stamp).total_seconds()<=9000:raise ValueError("stale")
    except (KeyError,TypeError,ValueError):
        report["blockers"].append("stale_or_invalid_feed")
        return report
    predictions={(str(p["event_id"]),str(p["team"])):p["win_probability"] for p in model.get("predictions",[]) if p.get("event_id") and p.get("team") and isinstance(p.get("win_probability"),(int,float)) and 0<p["win_probability"]<1}
    groups={}
    for r in odds.get("odds",[]):
        try:
            if r["market"]!="h2h":continue
            tip=dt.datetime.fromisoformat(r["commence_time"].replace("Z","+00:00"))
            updated=dt.datetime.fromisoformat(r["updated_at"].replace("Z","+00:00"))
            if tip<=now or not 0<=(now-updated).total_seconds()<=9000:continue
            groups.setdefault((str(r["event_id"]),str(r["bookmaker"])),[]).append(r)
        except (KeyError,TypeError,ValueError):continue
    for (event,book),rows in groups.items():
        names=str(rows[0].get("event","")).split(" @ ")
        if len(names)!=2 or len(rows)!=2 or {str(r.get("selection")) for r in rows}!=set(names):continue
        for r in rows:
            p=predictions.get((event,str(r["selection"])))
            if p is None:continue
            price=int(r["price"])
            if price==0:continue
            seed=int(hashlib.sha256((event+book+str(r["selection"])).encode()).hexdigest()[:16],16)
            rng=random.Random(seed)
            mc=sum(rng.random()<p for _ in range(draws))/draws
            report["games"].append({"event_id":event,"team":r["selection"],"bookmaker":book,"price":price,"model_probability":p,"mc_probability":round(mc,5),"mc_standard_error":round(math.sqrt(mc*(1-mc)/draws),6),"fair_decimal":round(1/p,4),"single_leg_ev":round(p*decimal(price)-1,5),"stress_ev_minus_3pp":round(max(.001,p-.03)*decimal(price)-1,5),"stress_ev_minus_5pp":round(max(.001,p-.05)*decimal(price)-1,5),"betting_eligible":False})
    for book in sorted({g["bookmaker"] for g in report["games"]}):
        eligible=sorted((g for g in report["games"] if g["bookmaker"]==book and g["single_leg_ev"]>0 and g["stress_ev_minus_3pp"]>0),key=lambda g:-g["single_leg_ev"])
        distinct=[];seen=set()
        for g in eligible:
            if g["event_id"] not in seen:distinct.append(g);seen.add(g["event_id"])
        for count in range(2,min(5,len(distinct))+1):
            legs=distinct[:count];rng=random.Random(1984+count+sum(map(ord,book)))
            mc=sum(all(rng.random()<leg["model_probability"] for leg in legs) for _ in range(draws))/draws
            report["parlays"].append({"bookmaker":book,"legs":[{"event_id":g["event_id"],"team":g["team"]} for g in legs],"independent_mc_probability":round(mc,5),"independent_model_product":round(math.prod(g["model_probability"] for g in legs),5),"stress_probability_minus_3pp":round(math.prod(max(.001,g["model_probability"]-.03) for g in legs),5),"correlation_verified":False,"executable_parlay_quote_verified":False,"betting_eligible":False})
    report["status"]="simulated_not_bet_eligible"
    report["blockers"]=sorted(set(report["blockers"]+["correlation_model_unverified","executable_parlay_quote_unavailable"]))
    return report

def main():
    def load(p):
        try:return json.loads(pathlib.Path(p).read_text())
        except (OSError,ValueError):return {}
    result=build(load("feed/basketball_nba.json"),load("feed/nba_ml_predictions.json"),load("feed/nba_ml_betting_readiness.json"),dt.datetime.now(dt.timezone.utc))
    p=pathlib.Path("feed/nba_ml_simulation_audit.json");p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(result,indent=2)+"\n")
    print(result["status"],len(result["games"]),"games",len(result["parlays"]),"parlays")
if __name__=="__main__":main()
