#!/usr/bin/env python3
"""Audit independent, reproducible old-vs-new NFL prop calibration evidence."""
import json
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def audit(forecasts, outcomes):
    verified={(o["event_id"],o["player"].lower(),o["market"]):o for o in outcomes if o.get("outcome_verified") is True}
    matched={}; missing=0; invalid=0
    for f in forecasts:
        key=(f.get("event_id"),str(f.get("player","")).lower(),f.get("market"))
        o=verified.get(key)
        if o is None:continue
        if f.get("forecast_at","")>=f.get("kickoff",""):invalid+=1;continue
        n=f.get("source_games")
        if not isinstance(n,int) or isinstance(n,bool) or n<8:
            missing+=1;continue
        p=f.get("model_probability")
        if not isinstance(p,(float,int)) or not 0<=p<=1:invalid+=1;continue
        if f.get("model_version")!="2025-prior-season-laplace-v1":invalid+=1;continue
        # One earliest archived forecast per player/game/market, independent of books and repeated snapshots.
        unique=key
        if unique not in matched or f["forecast_at"]<matched[unique][0]["forecast_at"]:matched[unique]=(f,o)
    games={k[0] for k in matched}
    scores=defaultdict(list)
    for f,o in matched.values():
        n=f["source_games"];old=f["model_probability"]
        hits=old*(n+2)-1
        # Reject non-reconstructible prior snapshots, rather than guessing historical sample sizes.
        if abs(hits-round(hits))>1e-6 or not 0<=hits<=n:invalid+=1;continue
        new=(round(hits)+4)/(n+8)
        y=int(float(o["outcome"])>float(f["line"]))
        scores["old"].append((old-y)**2);scores["revised"].append((new-y)**2)
    count=len(scores["old"])
    return {"status":"COMPARABLE" if len(games)>=2 and count>=20 else "INSUFFICIENT_EVIDENCE",
            "unique_games":len(games),"independent_scored_markets":count,
            "matched_forecasts_missing_source_games":missing,"invalid_or_unreconstructible":invalid,
            "old_brier":sum(scores["old"])/count if count else None,
            "revised_brier":sum(scores["revised"])/count if count else None,
            "bet_eligibility":"BLOCKED"}

def main():
    f=json.loads((ROOT/"feed/nfl_prop_forecast_ledger.json").read_text())["forecasts"]
    o=json.loads((ROOT/"feed/nfl_prop_verified_outcomes.json").read_text())
    print(json.dumps(audit(f,o),indent=2))
if __name__=="__main__":main()
