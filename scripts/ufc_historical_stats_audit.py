#!/usr/bin/env python3
"""Audit raw UFC fight-stat CSV; never present completed-fight stats as pre-fight."""
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

def audit(path, bouts_path=None):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader=csv.DictReader(fh)
        columns=reader.fieldnames or []
        if not columns or len(columns)!=len(set(columns)):
            raise ValueError("Missing or duplicate columns")
        rows=0
        empty=Counter()
        identities=Counter()
        invalid_reasons=Counter()
        round_examples=[]
        seen=set()
        verified=set()
        matched=set()
        if bouts_path:
            bouts=json.loads(Path(bouts_path).read_text())["results"]
            verified={(b["event_id"],frozenset((b["winner"],b["loser"]))) for b in bouts}
        for row in reader:
            if None in row:
                raise ValueError("Malformed CSV row")
            rows+=1
            event=(row.get("EVENT") or "").strip()
            pair=[x.strip() for x in (row.get("BOUT") or "").split(" vs. ")]
            fighter=(row.get("FIGHTER") or "").strip()
            rnd=(row.get("ROUND") or "").strip()
            if not event: invalid_reasons["missing_event"]+=1
            if len(pair)!=2 or len(set(pair))!=2: invalid_reasons["bad_bout"]+=1
            if fighter not in pair: invalid_reasons["fighter_not_in_bout"]+=1
            round_match=re.fullmatch(r"(?:Round )?([1-5])",rnd)
            if round_match is None: 
                invalid_reasons["non_numeric_round"]+=1
                if rnd not in round_examples and len(round_examples)<8: round_examples.append(rnd)
            if not event or len(pair)!=2 or len(set(pair))!=2 or fighter not in pair or round_match is None:
                identities["invalid_rows"]+=1
            else:
                key=(event,frozenset(pair),fighter,int(round_match.group(1)))
                if key in seen:
                    identities["duplicate_rows"]+=1
                seen.add(key)
                bout_key=(event,frozenset(pair))
                if bout_key in verified:
                    identities["matched_rows"]+=1
                    matched.add(bout_key)
                else:
                    identities["unmatched_rows"]+=1
            for col in columns:
                if not (row.get(col) or "").strip():
                    empty[col]+=1
    if not rows:
        raise ValueError("Empty fighter-stat feed")
    return {"status":"RAW_FIGHT_STATS_AVAILABLE_RESEARCH_ONLY",
            "source":"Greco1899/scrape_ufc_stats/ufc_fight_stats.csv",
            "rows":rows,"columns":columns,"empty_by_column":dict(empty),
            "identity_audit":dict(identities),"invalid_reasons":dict(invalid_reasons),
            "round_format_examples":round_examples,"matched_verified_bouts":len(matched),
            "verified_bouts":len(verified),"identity_matching_performed":bool(bouts_path),
            "pre_fight_feature_ready":False,
            "matched_to_verified_bouts":False,
            "leakage_safe_chronological_aggregates_ready":False,
            "deployed_to_live_predictions":False,
            "limitations":["Completed-fight statistics are not pre-fight features",
                           "Validate fighter/bout identities, duplicates and event chronology before modeling",
                           "Public mirror does not independently verify underlying measurements"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--bouts")
    args=p.parse_args()
    report=audit(args.input,args.bouts)
    Path(args.output).write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))
if __name__=="__main__":
    main()
