#!/usr/bin/env python3
"""Convert jansen88 UFC historical odds to conservative Elo archive candidates.

Scrape timestamps are NOT price timestamps. This source is retrospective,
so it cannot by itself satisfy independent point-in-time betting certification.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

def convert(rows):
    result=[]
    audit={"source_rows":len(rows),"matched_candidates":0,"excluded_missing_prices":0,
           "excluded_ambiguous_outcome":0,"excluded_duplicate":0}
    seen=set()
    for row in rows:
        event=(row.get("event_name") or "").strip()
        date=(row.get("event_date") or "").strip()
        f1=(row.get("fighter1") or "").strip()
        f2=(row.get("fighter2") or "").strip()
        favourite=(row.get("favourite") or "").strip()
        underdog=(row.get("underdog") or "").strip()
        outcome=(row.get("outcome") or "").strip().lower()
        if outcome not in ("fighter1","fighter2") or not event or not date or not f1 or not f2 or f1==f2:
            audit["excluded_ambiguous_outcome"]+=1
            continue
        if {f1,f2}!={favourite,underdog}:
            audit["excluded_missing_prices"]+=1
            continue
        try:
            fav=float(row["favourite_odds"])
            dog=float(row["underdog_odds"])
            if not (1<fav<100 and 1<dog<100):
                raise ValueError()
        except (ValueError,TypeError,KeyError):
            audit["excluded_missing_prices"]+=1
            continue
        key=(event,date,tuple(sorted((f1,f2))))
        if key in seen:
            audit["excluded_duplicate"]+=1
            continue
        seen.add(key)
        winner=f1 if outcome=="fighter1" else f2
        loser=f2 if outcome=="fighter1" else f1
        result.append({"event_name":event,"event_date":date,"winner":winner,"loser":loser,
                       "winner_decimal_odds":fav if winner==favourite else dog,
                       "loser_decimal_odds":dog if winner==favourite else fav,
                       "odds_source":"jansen88/ufc-data (betmma.tips retrospective scrape)",
                       "source_verified":False,"pre_fight_verified":False,
                       "odds_extract_ts":row.get("odds_extract_ts"),
                       "candidate_id":hashlib.sha256(str(key).encode()).hexdigest()[:20]})
    audit["matched_candidates"]=len(result)
    return {"schema":1,"sport":"UFC","bet_eligible":False,
            "independently_verified":False,
            "limitations":["Historical scrape timestamps do not prove prices existed before fight start",
                           "Names and event IDs require separate cross-source matching",
                           "No fabricated source_verified or pre_fight_verified flags"],
            "audit":audit,"odds_candidates":result}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    with open(a.input,encoding="utf-8-sig",newline="") as f:
        data=convert(list(csv.DictReader(f)))
    path=Path(a.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps(data["audit"],sort_keys=True))
if __name__=="__main__":
    main()
