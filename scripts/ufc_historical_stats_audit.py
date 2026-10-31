#!/usr/bin/env python3
"""Audit raw UFC fight-stat CSV; never present completed-fight stats as pre-fight."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

def audit(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader=csv.DictReader(fh)
        columns=reader.fieldnames or []
        if not columns or len(columns)!=len(set(columns)):
            raise ValueError("Missing or duplicate columns")
        rows=0
        empty=Counter()
        for row in reader:
            if None in row:
                raise ValueError("Malformed CSV row")
            rows+=1
            for col in columns:
                if not (row.get(col) or "").strip():
                    empty[col]+=1
    if not rows:
        raise ValueError("Empty fighter-stat feed")
    return {"status":"RAW_FIGHT_STATS_AVAILABLE_RESEARCH_ONLY",
            "source":"Greco1899/scrape_ufc_stats/ufc_fight_stats.csv",
            "rows":rows,"columns":columns,"empty_by_column":dict(empty),
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
    args=p.parse_args()
    report=audit(args.input)
    Path(args.output).write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))
if __name__=="__main__":
    main()
