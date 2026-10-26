#!/usr/bin/env python3
"""Leakage-safe replay of archived NFL pregame prop forecasts.

Never manufactures missing historical lines or predictions. Deduplicates
bookmaker quotes, scores directional hit rate, Brier score and flat-stake ROI.
"""
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
ROOT=Path(__file__).resolve().parent.parent
def dt(v):return datetime.fromisoformat(v.replace("Z","+00:00"))
def main():
    ledger=json.loads((ROOT/"feed/nfl_prop_forecast_ledger.json").read_text())["forecasts"]
    outcomes=json.loads((ROOT/"feed/nfl_prop_verified_outcomes.json").read_text())
    verified={(x["event_id"],x["player"].casefold(),x["market"]):x for x in outcomes if x.get("outcome_verified") is True and x.get("espn_event_id")}
    eligible=[];reasons=defaultdict(int)
    for f in ledger:
        try:
            if not(dt(f["quoted_at"])<=dt(f["forecast_at"])<dt(f["kickoff"])):reasons["non_pregame_timing"]+=1;continue
            if not(0<=float(f["model_probability"])<=1):reasons["invalid_probability"]+=1;continue
        except (KeyError,ValueError,TypeError):reasons["invalid_provenance"]+=1;continue
        k=(f["event_id"],f["player"].casefold(),f["market"])
        x=verified.get(k)
        if not x:reasons["no_independently_verified_outcome"]+=1;continue
        eligible.append((f,x))
    # One forecast per unique prop+book+line, earliest snapshot; avoid inflating
    # performance with repeated quotes at the same line.
    chosen={}
    for f,x in sorted(eligible,key=lambda v:v[0]["forecast_at"]):
        k=(f["event_id"],f["player"].casefold(),f["market"],f["bookmaker"],f["line"])
        if k not in chosen:chosen[k]=(f,x)
        else:reasons["duplicate_quote"]+=1
    results=[]
    for f,x in chosen.values():
        actual=float(x["outcome"]);line=float(f["line"]);p=float(f["model_probability"])
        side="over" if p>=.5 else "under"
        win=actual>line if side=="over" else actual<line
        push=actual==line
        odds=f.get("over_odds") if side=="over" else f.get("under_odds")
        profit=None
        if isinstance(odds,int) and (odds>=100 or odds<=-100):
            profit=0 if push else (odds/100 if odds>0 else 100/abs(odds)) if win else -1
        results.append({"game":x.get("event"),"player":f["player"],"market":f["market"],"bookmaker":f["bookmaker"],"line":line,"side":side,"model_probability_side":max(p,1-p),"actual":actual,"result":"PUSH" if push else "WIN" if win else "LOSS","profit_units":profit,"forecast_at":f["forecast_at"],"espn_event_id":x["espn_event_id"]})
    decided=[x for x in results if x["result"]!="PUSH"]
    bets=[x for x in results if x["profit_units"] is not None]
    brier=sum((x["model_probability_side"]-(1 if x["result"]=="WIN" else 0))**2 for x in decided)/len(decided) if decided else None
    roi=sum(x["profit_units"] for x in bets)/len(bets) if bets else None
    report={"method":"ARCHIVED_PREGAME_REPLAY","status":"RESEARCH_ONLY","date":"2026-10-25","scope":"Only independently verified archived forecasts, not full-slate historical reconstruction","archived_rows":len(ledger),"verified_unique_book_line_forecasts":len(results),"wins":sum(x["result"]=="WIN" for x in results),"losses":sum(x["result"]=="LOSS" for x in results),"pushes":sum(x["result"]=="PUSH" for x in results),"win_rate":sum(x["result"]=="WIN" for x in decided)/len(decided) if decided else None,"brier_score":brier,"flat_stake_roi":roi,"games_graded":len({x["espn_event_id"] for x in results}),"exclusions":dict(reasons),"results":results,"warning":"Correlated props and repeated markets are not independent samples. No out-of-sample full-slate performance is claimed."}
    out=ROOT/"feed/nfl_archived_replay_20261025.json";out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="results"}))
if __name__=="__main__":main()
