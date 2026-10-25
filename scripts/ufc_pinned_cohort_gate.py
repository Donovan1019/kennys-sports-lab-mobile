#!/usr/bin/env python3
"""Fail-closed cohort identity check for the pinned UFC historical benchmark."""
import argparse,json
from pathlib import Path
FIELDS=("joined_eligible_fights","holdout_date_scoped_fights","holdout_fight_ids_sha256","evaluated_fights","holdout_start_date")
def validate(expected,actual):
    if actual.get("source_snapshot_locked") is not True or actual.get("source_drift_gate")!="PASS":
        raise ValueError("SOURCE_NOT_PINNED")
    for key in FIELDS:
        if type(actual.get(key)) is not type(expected.get(key)) or actual.get(key)!=expected.get(key):
            raise ValueError("COHORT_DRIFT_BLOCKED: "+key)
    return {"cohort_gate":"PASS","checked_fields":list(FIELDS),"holdout_fight_ids_sha256":actual["holdout_fight_ids_sha256"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--expected",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    expected=json.loads(a.expected.read_text())
    actual=json.loads(a.report.read_text())
    result=validate(expected,actual)
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
