#!/usr/bin/env python3
"""Strict historical UFC bout adapter. Consumes a user-supplied verified results JSON; never fabricates data."""
import datetime as dt
import json
from collections import defaultdict
from pathlib import Path

METHODS={"KO/TKO","Submission","Decision"}

def normalize(records, as_of):
    if not isinstance(records,list):
        raise ValueError("Expected list of historical bouts")
    clean=[]
    seen=set()
    for row in records:
        if not isinstance(row,dict):
            continue
        required=("event_id","fight_id","event_date","winner","loser","method","source_url")
        if any(not isinstance(row.get(k),str) or not row[k].strip() for k in required):
            continue
        if row["method"] not in METHODS or row["winner"]==row["loser"]:
            continue
        try:
            when=dt.datetime.fromisoformat(row["event_date"].replace("Z","+00:00"))
        except ValueError:
            continue
        if when.tzinfo is None or when>=as_of:
            continue
        key=(row["event_id"],row["fight_id"])
        if key in seen:
            continue
        seen.add(key)
        clean.append(row)
    return clean

def summarize(records,as_of):
    rows=normalize(records,as_of)
    counts=defaultdict(lambda:{"wins":0,"losses":0,"KO/TKO":0,"Submission":0,"Decision":0})
    for row in rows:
        winner,loser=row["winner"],row["loser"]
        counts[winner]["wins"]+=1
        counts[loser]["losses"]+=1
        counts[winner][row["method"]]+=1
    fighters=[]
    for name,values in sorted(counts.items()):
        wins=values["wins"]
        # A fighter's victory method distribution is only descriptive, not a predictive probability.
        rates={m:values[m]/wins if wins else None for m in METHODS}
        fighters.append({"name":name,"wins":wins,"losses":values["losses"],
                         "verified_bout_count":wins+values["losses"],"win_method_counts":{m:values[m] for m in METHODS},
                         "historical_win_method_rates":rates,"bet_eligible":False})
    return {"schema":1,"sport":"UFC","as_of":as_of.isoformat(),"verified_result_count":len(rows),
            "fighters":fighters,"research_only":True,"bet_eligible":False,
            "warning":"Descriptive UFC fight results only. No opponent adjustment, odds, or calibrated probabilities."}

def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",required=True,help="Locally verified source results JSON")
    parser.add_argument("--output",default="feed/ufc_fighter_history.json")
    args=parser.parse_args()
    payload=json.loads(Path(args.input).read_text())
    result=summarize(payload["results"],dt.datetime.now(dt.timezone.utc))
    output=Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+"\n")
    print(f"Validated {result['verified_result_count']} unique completed UFC bouts")

if __name__=="__main__":
    main()
