#!/usr/bin/env python3
"""Retrospective scheduled-round vs realized-duration consistency diagnostic.

This does not establish scheduled-round provenance or authorize betting.
"""
import argparse,json
from collections import Counter
from pathlib import Path
from scripts.ufc_native_fight_join import BASE,fetch,join

def audit(records):
    totals=Counter();examples=[];missing=0;invalid=0
    for record in records:
        f=record["wide_record"];raw=str(f.get("scheduled_rounds","")).strip()
        if not raw:missing+=1;continue
        if raw not in ("3","5"):invalid+=1;continue
        try:duration=float(f["fight_duration_sec"])
        except (ValueError,TypeError,KeyError):invalid+=1;continue
        if not 0<duration<=1500:invalid+=1;continue
        rounds=int(raw);totals[f"{rounds}_round_fights"]+=1
        if duration>rounds*300:
            totals["duration_exceeds_scheduled_max"]+=1
            if len(examples)<20:examples.append({"fight_id":record["ufcstats_fight_id"],"scheduled_rounds":rounds,"duration_seconds":duration})
        if duration==rounds*300:totals[f"{rounds}_round_full_duration"]+=1
    return {"schema":1,"total_records":len(records),"counts":dict(totals),
      "missing":missing,"invalid":invalid,"exceedance_examples":examples,
      "source_semantics_verified":False,"bet_eligible":False,
      "limitations":"Internal plausibility check only. Cannot independently establish that scheduled_rounds represents pre-bout scheduled rounds; no production use."}
def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    cross,_=fetch(BASE+"id_crosswalk_all.csv");wide,_=fetch(BASE+"ufc_all_fights_wide.csv")
    linked=join(cross,wide)
    if linked["status"]!="JOINED":raise SystemExit("join failed")
    report=audit(linked["records"])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
