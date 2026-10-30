#!/usr/bin/env python3
"""Convert Greco1899 UFCStats event/result CSVs into verified Elo input.

Fail closed on unknown outcome encodings, missing event dates, and ambiguous bouts.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

def load_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))

def event_date(value):
    value=value.strip()
    for fmt in ("%B %d, %Y","%b %d, %Y","%Y-%m-%d"):
        try:
            return dt.datetime.strptime(value,fmt).date().isoformat()+"T12:00:00+00:00"
        except ValueError:
            pass
    return None

def convert(events, fights):
    dates={}
    ambiguous=set()
    for e in events:
        name=(e.get("EVENT") or "").strip()
        date=event_date(e.get("DATE") or "")
        if not name or not date:
            continue
        if name in dates and dates[name]!=date:
            ambiguous.add(name)
        dates[name]=date
    output=[]
    counts={"source_fights":len(fights),"included":0,"excluded_missing_date":0,
            "excluded_unverified_result":0,"excluded_bad_bout":0,"excluded_duplicate":0}
    seen=set()
    for row in fights:
        name=(row.get("EVENT") or "").strip()
        if name not in dates or name in ambiguous:
            counts["excluded_missing_date"]+=1
            continue
        bout=(row.get("BOUT") or "").strip()
        fighters=bout.split(" vs. ")
        if len(fighters)!=2 or not all(x.strip() for x in fighters) or fighters[0]==fighters[1]:
            counts["excluded_bad_bout"]+=1
            continue
        # UFCStats stores the outcome for each fighter in listed bout order.
        # Reject draws, no-contests, and unexpected encodings.
        result=(row.get("OUTCOME") or "").strip().upper().replace(" ","")
        if result not in ("W/L","L/W"):
            counts["excluded_unverified_result"]+=1
            continue
        winner,loser=(fighters if result=="W/L" else fighters[::-1])
        key=(name,bout)
        if key in seen:
            counts["excluded_duplicate"]+=1
            continue
        seen.add(key)
        output.append({"event_id":name,"fight_id":hashlib.sha256((name+"|"+bout).encode()).hexdigest()[:24],
                       "event_date":dates[name],"winner":winner.strip(),"loser":loser.strip(),
                       "winner_verified":True})
    output.sort(key=lambda x:(x["event_date"],x["event_id"],x["fight_id"]))
    counts["included"]=len(output)
    return {"schema":1,"sport":"UFC","source":"Greco1899/scrape_ufc_stats",
            "research_only":True,"bet_eligible":False,"conversion_audit":counts,
            "limitations":["Event dates represented as UTC noon for chronological grouping; not actual fight start times",
                           "Winner verification depends on source outcome order and is not independently cross-checked"],
            "results":output}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--events",required=True)
    p.add_argument("--fights",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    payload=convert(load_csv(args.events),load_csv(args.fights))
    target=Path(args.output)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(payload,indent=2)+"\n")
    print(json.dumps(payload["conversion_audit"],sort_keys=True))
if __name__=="__main__":
    main()
