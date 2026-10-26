#!/usr/bin/env python3
"""Bridge existing immutable NFL forecasts and ESPN-verified outcomes into ledger grader.
No fresh price capture, no inferred player IDs, and no sportsbook availability claims.
"""
import json,sys
from pathlib import Path
from scripts.grade_nfl_pregame_ledger import grade
from scripts.validate_nfl_pregame_ledger import timestamp

MARKETS={"player_pass_yds","player_rush_yds","player_reception_yds","player_receptions"}
def decimal(american):
    if isinstance(american,bool) or not isinstance(american,(int,float)) or american==0 or -100<american<100:
        raise ValueError("invalid American odds")
    return 1+american/100 if american>0 else 1+100/abs(american)

def bridge(forecasts,outcomes):
    if not isinstance(forecasts,dict) or not isinstance(forecasts.get("forecasts"),list):
        raise ValueError("missing forecast ledger")
    if not isinstance(outcomes,list):raise ValueError("missing outcome archive")
    valid=[];rejected={};seen=set();unsupported=0
    for f in forecasts["forecasts"]:
        if f.get("market") not in MARKETS:
            unsupported+=1
            continue
        try:
            if not f.get("research_only"):raise ValueError("research_flag_missing")
            if not all(isinstance(f.get(k),str) and f[k] for k in ("forecast_id","event_id","player","bookmaker","model_version","quoted_at","forecast_at","kickoff")):
                raise ValueError("missing_identity_or_timestamp")
            if f["forecast_id"] in seen:raise ValueError("duplicate_forecast")
            seen.add(f["forecast_id"])
            if timestamp(f["quoted_at"])>timestamp(f["forecast_at"]) or timestamp(f["forecast_at"])>=timestamp(f["kickoff"]):
                raise ValueError("non_pregame_quote_or_forecast")
            if not f.get("source_commit"):raise ValueError("unversioned_forecast")
            for side,field in (("over","over_odds"),("under","under_odds")):
                valid.append({"snapshot_id":f["forecast_id"]+":"+side,"game_id":f["event_id"],
                  "player_id":f["player"],"market":f["market"],"side":side,"line":f["line"],
                  "decimal_odds":decimal(f[field]),"probability":f["model_probability"] if side=="over" else 1-f["model_probability"],
                  "captured_at":f["forecast_at"],"kickoff_at":f["kickoff"],
                  "source":f["bookmaker"]+"|"+f["source_commit"],"model_version":f["model_version"]})
        except (ValueError,TypeError,KeyError) as exc:
            rejected[str(exc)]=rejected.get(str(exc),0)+1
    verified=[];unverified=0
    for o in outcomes:
        if not isinstance(o,dict) or o.get("market") not in MARKETS:continue
        if o.get("outcome_verified") is not True or not o.get("espn_event_id") or not str(o.get("source","")).startswith("https://"):
            unverified+=1;continue
        try:
            timestamp(o["kickoff"])
            verified.append({"game_id":o["event_id"],"player_id":o["player"],"market":o["market"],
                             "actual":o["outcome"],"final_at":o["verified_at"].replace("+00:00","Z")})
        except (ValueError,KeyError,TypeError):unverified+=1
    if rejected:
        return {"status":"BLOCKED","reason":"Forecast rows rejected; refusing partial sample selection","rejected":rejected,"bet_eligibility":"BLOCKED"}
    report=grade(valid,verified)
    report["bridge"]={"forecast_rows":len(forecasts["forecasts"]),"excluded_unsupported_market_forecasts":unsupported,"snapshots":len(valid),"verified_outcome_rows":len(verified),"excluded_unverified_outcomes":unverified,
                       "source":"existing pregame forecast ledger and ESPN-verified outcomes"}
    report["warning"]="Research only. Existing forecasts use prior-season Laplace probabilities; no independent bookmaker feed verification or live deployment."
    return report

if __name__=="__main__":
    root=Path(__file__).resolve().parent.parent
    a=json.loads((root/"feed/nfl_prop_forecast_ledger.json").read_text())
    b=json.loads((root/"feed/nfl_prop_verified_outcomes.json").read_text())
    print(json.dumps(bridge(a,b),indent=2))
