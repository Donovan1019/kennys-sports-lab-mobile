#!/usr/bin/env python3
"""Offline, fail-closed visibility into NFL pregame forecast archive and graded evidence."""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(name):
    return json.loads((ROOT/name).read_text(encoding="utf-8"))
def inspect(ledger, graded, coverage):
    forecasts=ledger.get("forecasts") if isinstance(ledger,dict) else None
    if not isinstance(forecasts,list) or not isinstance(graded,list):
        raise ValueError("Invalid NFL forecast ledger or graded archive schema")
    ids=[x.get("forecast_id") for x in forecasts]
    if any(not isinstance(x,str) or not x for x in ids) or len(set(ids))!=len(ids):
        raise ValueError("Duplicate or missing forecast IDs in pregame ledger")
    graded_ids={x.get("forecast_id") for x in graded if isinstance(x,dict) and x.get("outcome_verified") is True}
    awaiting=sum(1 for x in ids if x not in graded_ids)
    markets=dict(Counter(str(x.get("market")) for x in forecasts))
    # Only immutable archived pregame forecasts with independently verified grades
    # may enter forward calibration. Never use unlinked historical results.
    by_id={x["forecast_id"]:x for x in forecasts}
    verified=[]
    for row in graded:
        if not isinstance(row,dict) or row.get("outcome_verified") is not True:continue
        f=by_id.get(row.get("forecast_id"))
        if not f:continue
        p=f.get("model_probability")
        outcome=row.get("over_hit")
        if not isinstance(p,(int,float)) or isinstance(p,bool) or not 0<=p<=1 or type(outcome) is not bool:continue
        try:
            forecast_at=datetime.fromisoformat(f["forecast_at"].replace("Z","+00:00"))
            kickoff=datetime.fromisoformat(f["kickoff"].replace("Z","+00:00"))
            if forecast_at.tzinfo is None or kickoff.tzinfo is None or forecast_at>=kickoff:continue
        except (KeyError,TypeError,ValueError,AttributeError):continue
        verified.append((p,int(outcome)))
    brier=sum((p-y)**2 for p,y in verified)/len(verified) if verified else None
    return {
        "status":"RESEARCH_ONLY",
        "pregame_forecasts_archived":len(forecasts),
        "verified_graded_rows":sum(x.get("outcome_verified") is True for x in graded if isinstance(x,dict)),
        "archived_forecasts_awaiting_verified_grade":awaiting,
        "forecast_markets":markets,
        "capture_status":coverage.get("status","UNKNOWN") if isinstance(coverage,dict) else "UNKNOWN",
        "captured_events":coverage.get("captured_events",0) if isinstance(coverage,dict) else 0,
        "expected_upcoming_events":coverage.get("expected_upcoming_events",0) if isinstance(coverage,dict) else 0,
        "matched_verified_forward_grades":len(verified),
        "forward_brier_score":brier,
        "forward_calibration_approved":False,
        "bet_eligibility":"BLOCKED",
        "limitations":"Verified graded historical rows can predate the current append-only forecast ledger. Counts are not a predictive edge or authorization to wager."
    }
def main():
    result=inspect(read("feed/nfl_prop_forecast_ledger.json"),read("feed/nfl_prop_graded_snapshots.json"),read("feed/nfl_prop_capture_coverage.json"))
    dest=ROOT/"feed/nfl_prop_archive_health.json"
    dest.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
