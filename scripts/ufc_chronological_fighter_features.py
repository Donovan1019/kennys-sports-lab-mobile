#!/usr/bin/env python3
"""Research-only, leakage-safe historical UFC pre-fight fighter averages."""
import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

def count(value):
    match=re.fullmatch(r"\s*(\d+)\s+of\s+(\d+)\s*",value or "")
    if not match:
        return None
    landed,attempted=map(int,match.groups())
    return landed if landed<=attempted else None

def build(bouts,stat_rows):
    by_bout=defaultdict(list)
    verified={}
    for bout in bouts:
        key=(bout["event_id"],frozenset((bout["winner"],bout["loser"])))
        if key in verified:
            raise ValueError("Duplicate verified bout identity")
        verified[key]=bout
    for row in stat_rows:
        pair=[v.strip() for v in (row.get("BOUT") or "").split(" vs. ")]
        fighter=(row.get("FIGHTER") or "").strip()
        rnd=re.fullmatch(r"(?:Round )?([1-5])",(row.get("ROUND") or "").strip())
        if len(pair)!=2 or len(set(pair))!=2 or fighter not in pair or not rnd:
            continue
        key=((row.get("EVENT") or "").strip(),frozenset(pair))
        if key not in verified:
            continue
        sig=count(row.get("SIG.STR."))
        td=count(row.get("TD"))
        if sig is None or td is None:
            continue
        by_bout[key].append((fighter,int(rnd.group(1)),sig,td))
    history=defaultdict(list)
    outputs=[]
    excluded=defaultdict(int)
    events=defaultdict(list)
    for key,bout in verified.items():
        events[bout["event_date"]].append((key,bout))
    for date in sorted(events):
        pending=[]
        for key,bout in events[date]:
            rows=by_bout.get(key,[])
            keys=[(fighter,rnd) for fighter,rnd,_,_ in rows]
            if len(keys)!=len(set(keys)):
                excluded["duplicate_fighter_round"]+=1
                continue
            fighters=(bout["winner"],bout["loser"])
            per={}
            for fighter in fighters:
                rounds=[(sig,td) for name,_,sig,td in rows if name==fighter]
                if not rounds:
                    break
                per[fighter]={"sig_strikes_landed":sum(v[0] for v in rounds),
                             "takedowns_landed":sum(v[1] for v in rounds),
                             "rounds":len(rounds)}
            if len(per)!=2:
                excluded["incomplete_fighter_stats"]+=1
                continue
            features={}
            for fighter in fighters:
                previous=history[fighter]
                features[fighter]={"prior_fights":len(previous),
                    "prior_sig_strikes_per_recorded_round":sum(x["sig_strikes_landed"] for x in previous)/sum(x["rounds"] for x in previous) if previous else None,
                    "prior_takedowns_per_recorded_round":sum(x["takedowns_landed"] for x in previous)/sum(x["rounds"] for x in previous) if previous else None}
            outputs.append({"fight_id":bout["fight_id"],"event_date":date,"winner":fighters[0],
                            "loser":fighters[1],"pre_fight":features})
            pending.append(per)
        # Freeze same-date snapshots: no fighter can learn from a fight on the same event date.
        for per in pending:
            for fighter,stats in per.items():
                history[fighter].append(stats)
    return {"status":"RESEARCH_ONLY_NOT_BET_ELIGIBLE","source":"Greco1899/scrape_ufc_stats",
            "features":outputs,"matched_complete_bouts":len(outputs),
            "excluded":dict(excluded),"live_predictions_updated":False,
            "limitations":["Raw per-round totals, not opponent-adjusted or per-minute rates",
                           "Same-date bouts excluded from each other's pre-fight history",
                           "No model backtest or independent sportsbook validation yet"]}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--bouts",required=True)
    parser.add_argument("--stats",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    bouts=json.loads(Path(args.bouts).read_text())["results"]
    with open(args.stats,encoding="utf-8-sig",newline="") as f:
        stats=list(csv.DictReader(f))
    report=build(bouts,stats)
    Path(args.output).write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="features"}))
if __name__=="__main__":
    main()
