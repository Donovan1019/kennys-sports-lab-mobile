#!/usr/bin/env python3
"""Pre-event UFC Elo research probabilities from historical TidyTuesday outcomes.

Historical source is NOT independently verified. Ratings are descriptive research
only; no current status, round count, sportsbook price, or betting eligibility.
"""
import argparse
import datetime as dt
import json
import math
from collections import defaultdict
from pathlib import Path

def build(snapshot,card,as_of=None,k=48,min_bouts=8):
    if snapshot.get("snapshot")!="2026-07-07" or snapshot.get("bet_eligible") is not False:
        raise ValueError("Unexpected historical snapshot")
    if card.get("sport")!="UFC" or card.get("bet_eligible") is not False:
        raise ValueError("Unexpected fight card")
    as_of=as_of or dt.datetime.now(dt.timezone.utc)
    if not 0<k<=100 or not 1<=min_bouts<=100:raise ValueError("Invalid Elo parameters")
    rows=defaultdict(list)
    seen=set()
    for f in snapshot.get("fight_history",{}).get("rows",[]):
        try:
            date=dt.date.fromisoformat(f["event_date"])
            w,l=f["winner"],f["loser"]
            key=f["source_fight_url"]
            if f.get("independently_verified") is not False or not w or not l or w==l or key in seen or date>=as_of.date():continue
        except (KeyError,ValueError,TypeError):continue
        seen.add(key);rows[date].append((w,l))
    ratings={};bouts=defaultdict(int)
    for day in sorted(rows):
        changes=defaultdict(float);counts=defaultdict(int)
        for w,l in rows[day]:
            a=ratings.get(w,1500.);b=ratings.get(l,1500.)
            p=1/(1+10**((b-a)/400))
            changes[w]+=k*(1-p);changes[l]-=k*(1-p)
            counts[w]+=1;counts[l]+=1
        for name,delta in changes.items():ratings[name]=ratings.get(name,1500.)+delta
        for name,n in counts.items():bouts[name]+=n
    out=[]
    for f in card.get("fights",[]):
        a,b=f.get("red"),f.get("blue")
        if not a or not b or a==b:continue
        na,nb=bouts[a],bouts[b]
        eligible=na>=min_bouts and nb>=min_bouts
        p=1/(1+10**((ratings.get(b,1500.)-ratings.get(a,1500.))/400)) if eligible else None
        out.append({"fight_id":f.get("id"),"red":a,"blue":b,"start_time":f.get("start_time"),
                    "red_prior_bouts":na,"blue_prior_bouts":nb,
                    "red_elo":round(ratings[a],2) if na else None,
                    "blue_elo":round(ratings[b],2) if nb else None,
                    "red_research_probability":round(p,6) if p is not None else None,
                    "blue_research_probability":round(1-p,6) if p is not None else None,
                    "status":"HISTORICAL_RESEARCH_ONLY" if eligible else "INSUFFICIENT_MATCHED_HISTORY",
                    "bet_eligible":False})
    return {"schema":1,"sport":"UFC","model":"TidyTuesday historical Elo K48 min8",
            "as_of":as_of.isoformat(),"historical_source_independently_verified":False,
            "identity_matching":"exact normalized source names only",
            "research_only":True,"bet_eligible":False,"projections":out,
            "limitations":["Historical source identity and result completeness not independently verified",
                           "No live fighter role, injury, weigh-in, bout length, odds or method calibration",
                           "Elo probabilities are not validated betting probabilities"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--snapshot",default="feed/ufc_tidytuesday_research.json")
    p.add_argument("--card",default="feed/ufc_research.json")
    p.add_argument("--output",default="feed/ufc_elo_projections.json")
    a=p.parse_args()
    result=build(json.loads(Path(a.snapshot).read_text()),json.loads(Path(a.card).read_text()))
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2)+"\n")
    print("UFC research Elo rows:",len(result["projections"]),"with historical probabilities:",sum(x["red_research_probability"] is not None for x in result["projections"]))
if __name__=="__main__":main()
