#!/usr/bin/env python3
"""Grade verified pregame snapshots against externally supplied settled outcomes."""
import json,sys
from pathlib import Path
from scripts.validate_nfl_pregame_ledger import validate, timestamp

def grade(snapshots,results):
    integrity=validate(snapshots)
    if integrity["status"]!="VALID":
        return {"status":"BLOCKED","integrity":integrity,"bet_eligibility":"BLOCKED"}
    if not isinstance(results,list): raise ValueError("results must be a list")
    lookup={}
    for result in results:
        if not isinstance(result,dict): raise ValueError("result must be object")
        key=(result.get("game_id"),result.get("player_id"),result.get("market"))
        if key in lookup: raise ValueError("duplicate settlement key")
        value=result.get("actual")
        if isinstance(value,bool) or not isinstance(value,(int,float)) or value<0:
            raise ValueError("invalid settled value")
        if not isinstance(result.get("final_at"),str): raise ValueError("missing final_at")
        timestamp(result["final_at"])
        lookup[key]=result
    graded=[];pending=[]
    for s in snapshots:
        key=(s["game_id"],s["player_id"],s["market"])
        result=lookup.get(key)
        if result is None:
            pending.append(s["snapshot_id"]);continue
        if timestamp(result["final_at"])<=timestamp(s["kickoff_at"]):
            raise ValueError("settlement cannot precede kickoff")
        actual=result["actual"]
        if actual==s["line"]:
            outcome="push";profit=0;hit=None
        else:
            hit=(actual>s["line"]) if s["side"]=="over" else (actual<s["line"])
            outcome="win" if hit else "loss"
            profit=s["decimal_odds"]-1 if hit else -1
        graded.append({"snapshot_id":s["snapshot_id"],"outcome":outcome,"units":round(profit,6),
                       "brier":round((s["probability"]-int(hit))**2,6) if hit is not None else None})
    scored=[r for r in graded if r["brier"] is not None]
    return {"status":"RESEARCH_ONLY","graded":len(graded),"pending":len(pending),
            "pending_snapshot_ids":pending,"results":graded,
            "mean_brier":round(sum(r["brier"] for r in scored)/len(scored),6) if scored else None,
            "net_units":round(sum(r["units"] for r in graded),6),
            "bet_eligibility":"BLOCKED",
            "warning":"Supplied results and sportsbook snapshots are not independently authenticated. Historical unit returns do not prove future profitability."}

if __name__=="__main__":
    report=grade(json.loads(Path(sys.argv[1]).read_text()),json.loads(Path(sys.argv[2]).read_text()))
    print(json.dumps(report,indent=2))
    if report["status"]=="BLOCKED":sys.exit(1)
