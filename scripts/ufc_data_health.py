#!/usr/bin/env python3
"""Fail-closed UFC data-readiness audit for the daily research pipeline."""
import argparse
import datetime as dt
import json
from pathlib import Path

def audit(history,elo,holdout,now=None):
    now=now or dt.datetime.now(dt.timezone.utc)
    results=history.get("results",[])
    successful=history.get("successful_days",[])
    failed=history.get("failed_days",[])
    if not isinstance(results,list) or not isinstance(successful,list) or not isinstance(failed,list):
        raise ValueError("Malformed historical data")
    seen=set()
    invalid=0
    for row in results:
        if not isinstance(row,dict) or row.get("winner_verified") is not True or not all(row.get(k) for k in ("event_id","fight_id","winner","loser","event_date")):
            invalid+=1
            continue
        key=(str(row["event_id"]),str(row["fight_id"]))
        if key in seen or row["winner"]==row["loser"]:
            invalid+=1
        seen.add(key)
    verified=len(seen)
    graded=holdout.get("holdout_n",0)
    blockers=[]
    if not verified:blockers.append("NO_VERIFIED_HISTORICAL_FIGHTS")
    if invalid:blockers.append("INVALID_OR_DUPLICATE_HISTORICAL_ROWS")
    if not successful:blockers.append("NO_SUCCESSFUL_SOURCE_DAYS")
    if failed:blockers.append("SOURCE_FETCH_FAILURES")
    if not isinstance(graded,int) or graded<100:blockers.append("INSUFFICIENT_HOLDOUT")
    if elo.get("historical_bouts_used")!=verified:blockers.append("ELO_HISTORY_MISMATCH")
    if holdout.get("bet_eligible") is not False or elo.get("bet_eligible") is not False:
        blockers.append("RESEARCH_FLAG_INTEGRITY_FAILURE")
    blockers.append("NO_INDEPENDENT_PRICE_AND_CALIBRATION_APPROVAL")
    return {"schema":1,"sport":"UFC","generated_at":now.isoformat(),"verified_fights":verified,
            "successful_source_days":len(set(successful)),"failed_source_days":len(failed),
            "invalid_rows":invalid,"holdout_n":graded,"status":"BLOCKED" if blockers else "REVIEW",
            "blockers":blockers,"bet_eligible":False,
            "note":"Successful fetches are not proof of complete historical event coverage."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--history",default="feed/ufc_historical_backfill.json")
    p.add_argument("--elo",default="backtests/reports/ufc_elo_baseline.json")
    p.add_argument("--holdout",default="backtests/reports/ufc_holdout_readiness.json")
    p.add_argument("--output",default="backtests/reports/ufc_data_health.json")
    a=p.parse_args()
    result=audit(*[json.loads(Path(path).read_text()) for path in (a.history,a.elo,a.holdout)])
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print("UFC data readiness:",result["status"],"fights:",result["verified_fights"],"blockers:",",".join(result["blockers"]))
if __name__=="__main__":main()
