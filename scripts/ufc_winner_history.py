#!/usr/bin/env python3
"""Derive winner-only fighter records from completed verified UFC outcomes."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

def summarize_winners(rows):
    if not isinstance(rows,list):
        raise ValueError("Results must be a list")
    seen=set()
    counts=defaultdict(lambda:{"wins":0,"losses":0})
    excluded=0
    for row in rows:
        if not isinstance(row,dict) or row.get("winner_verified") is not True:
            excluded+=1
            continue
        eid,fid=row.get("event_id"),row.get("fight_id")
        winner,loser=row.get("winner"),row.get("loser")
        if not all(isinstance(x,str) and x.strip() for x in (eid,fid,winner,loser)) or winner==loser:
            excluded+=1
            continue
        key=(eid,fid)
        if key in seen:
            excluded+=1
            continue
        seen.add(key)
        counts[winner]["wins"]+=1
        counts[loser]["losses"]+=1
    return {"schema":1,"sport":"UFC","source":"Verified scoreboard winners only",
            "unique_completed_fights":len(seen),"excluded_rows":excluded,
            "fighters":[{"name":name,**record} for name,record in sorted(counts.items())],
            "method_probabilities_available":False,"opponent_adjusted":False,"bet_eligible":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",default="feed/ufc_winner_history.json")
    a=p.parse_args()
    rows=json.loads(Path(a.input).read_text())["results"]
    report=summarize_winners(rows)
    path=Path(a.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2)+"\n")
    print(f"Historical UFC winners: {report['unique_completed_fights']} verified bouts")
if __name__=="__main__":
    main()
