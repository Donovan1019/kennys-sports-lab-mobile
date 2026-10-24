#!/usr/bin/env python3
"""Audit whether joined source supplies a trustworthy scheduled-rounds field.

This audit never infers scheduled rounds from observed duration.
"""
import argparse,json
from collections import Counter
from pathlib import Path
from scripts.ufc_native_fight_join import BASE,fetch,join
CANDIDATES=("scheduled_rounds","num_rounds","total_rounds","bout_rounds","fight_scheduled_rounds")
def audit(records):
    columns=sorted({key for record in records for key in record["wide_record"]})
    candidates=[k for k in CANDIDATES if k in columns]
    counts=Counter()
    invalid=0
    for record in records:
        fields=record["wide_record"]
        values={str(fields.get(k,"")).strip() for k in candidates if str(fields.get(k,"")).strip()}
        if len(values)>1:
            invalid+=1;continue
        if not values:counts["missing"]+=1;continue
        value=values.pop()
        if value not in ("3","5"):invalid+=1;continue
        counts[value]+=1
    usable=bool(candidates) and invalid==0 and counts["missing"]==0
    return {"schema":1,"records":len(records),"candidate_fields":candidates,
      "available_columns":columns,"scheduled_rounds_counts":dict(counts),
      "invalid_or_conflicting":invalid,"complete_and_valid":usable,
      "verified_source_semantics":False,"ready_for_duration_model":False,
      "bet_eligible":False,
      "reason":"Column names and numeric values alone cannot establish scheduled-round semantics; independently verify source documentation before model use."}
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);args=p.parse_args()
    cross,_=fetch(BASE+"id_crosswalk_all.csv");wide,_=fetch(BASE+"ufc_all_fights_wide.csv")
    linked=join(cross,wide)
    if linked["status"]!="JOINED":raise SystemExit("fight join failed")
    report=audit(linked["records"])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="available_columns"},indent=2))
if __name__=="__main__":main()
