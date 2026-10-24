#!/usr/bin/env python3
"""Audit whether joined UFC fight records support safe fighter-level reconstruction.

A successful ID join is not a valid fighter-row model: report exact source columns,
fight dates, corner identities, round exposure and strikes/takedowns availability.
"""
import argparse,json,re
from pathlib import Path
from scripts.ufc_native_fight_join import fetch,join,BASE

def audit(records):
    if not records:raise ValueError("empty joined fight records")
    cols=set(records[0]["wide_record"])
    def candidates(*tokens):
        return sorted(c for c in cols if any(t in c.lower() for t in tokens))
    groups={
      "date":candidates("date","event_time"),
      "fighter_identity":candidates("fighter_id","f1_id","f2_id","r_fighter","b_fighter"),
      "strike_counts":candidates("sig_str","significant_strike"),
      "takedown_counts":candidates("takedown","_td_","td_landed","td_attempt"),
      "duration":candidates("duration","total_time","fight_time","last_round_time"),
      "winner":candidates("winner","result","outcome"),
      "rounds":candidates("round","rnd")
    }
    required=("date","strike_counts","takedown_counts","duration","winner")
    missing=[k for k in required if not groups[k]]
    return {"joined_fights":len(records),"wide_columns":sorted(cols),"feature_column_candidates":groups,
      "missing_required_groups":missing,
      "can_construct_pre_fight_features":False,
      "reason":"Retrospective records require explicit per-fight event chronology, fighter-side mappings, settlement and source publication checks before PIT approval"}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    cross,_=fetch(BASE+"id_crosswalk_all.csv")
    wide,_=fetch(BASE+"ufc_all_fights_wide.csv")
    linked=join(cross,wide)
    if linked["status"]!="JOINED":raise SystemExit("native ID join failed")
    report=audit(linked["records"])
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
