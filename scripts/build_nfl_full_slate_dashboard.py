#!/usr/bin/env python3
"""Publish truthful NFL full-slate archive, player eligibility and calibration summary."""
import json
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parent.parent
def read(path,default):
    p=ROOT/path
    return json.loads(p.read_text()) if p.exists() else default
def main():
    ledger=read("feed/nfl_prop_forecast_ledger.json",{}).get("forecasts",[])
    graded=read("feed/nfl_prop_graded_snapshots.json",[])
    coverage=read("feed/nfl_prop_capture_coverage.json",{})
    by_game=defaultdict(lambda:{"archived":0,"graded":0,"wins":0,"losses":0,"pushes":0})
    for f in ledger:
        game=f.get("event") or "UNMATCHED EVENT (LEGACY)"
        by_game[game]["archived"]+=1
    for f in graded:
        if f.get("outcome_verified") is not True:continue
        game=f.get("event") or "UNMATCHED EVENT (LEGACY)"
        d=by_game[game];d["graded"]+=1
        try:
            actual=float(f["outcome"]);line=float(f["line"]);p=float(f["model_probability"])
        except (ValueError,TypeError,KeyError):continue
        result="pushes" if actual==line else "wins" if ((actual>line)==(p>=.5)) else "losses"
        d[result]+=1
    unique={}
    for f in graded:
        if not f.get('outcome_verified'):continue
        try:
            actual=float(f['outcome']);line=float(f['line']);prob=float(f['model_probability'])
        except (KeyError,TypeError,ValueError):continue
        if not 0<=prob<=1:continue
        side='OVER' if prob>0.5 else 'UNDER' if prob<0.5 else 'NO_EDGE'
        key=(f.get('event_id'),f.get('player'),f.get('market'),line,side)
        if key not in unique:unique[key]=(actual,line,side,f.get('market'))
    counts={'wins':0,'losses':0,'pushes':0,'no_edge':0}
    for actual,line,side,market in unique.values():
        result='pushes' if actual==line else 'no_edge' if side=='NO_EDGE' else 'wins' if ((actual>line)==(side=='OVER')) else 'losses'
        counts[result]+=1
    deduplicated={'total':len(unique),**counts}
    # Research-only: no cross-game calibration until independent samples exist.
    games_with_grades=sum(v["graded"]>0 for v in by_game.values())
    output={"status":"RESEARCH_ONLY","betting_eligible":False,"readiness_reason":"Player roster/injury validation and multi-game out-of-sample calibration not complete","capture":coverage,"deduplicated":deduplicated,"archived_forecasts":len(ledger),"graded_forecasts":len(graded),"games_with_grades":games_with_grades,"game_results":[{"game":k,**v} for k,v in sorted(by_game.items())],"calibration_status":"INSUFFICIENT_CROSS_GAME_SAMPLE" if games_with_grades<10 else "REQUIRES_INDEPENDENT_CALIBRATION"}
    out=ROOT/"feed/nfl_full_slate_dashboard.json"
    out.write_text(json.dumps(output,indent=2)+chr(10))
    print(json.dumps({"archived":len(ledger),"graded":len(graded),"games_with_grades":games_with_grades,"status":output["status"]}))
if __name__=="__main__":main()
