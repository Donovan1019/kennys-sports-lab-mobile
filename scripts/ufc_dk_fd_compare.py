#!/usr/bin/env python3
"""Compare authorized DraftKings and FanDuel UFC moneyline snapshots.

This adapter reads supplied JSON exports; it does not scrape sportsbook sites.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
from scripts.ufc_odds_connector import normalize

PROVIDERS={"draftkings":"DraftKings","fanduel":"FanDuel"}

def compare(snapshots):
    by_event={}
    results={}
    for key in PROVIDERS:
        snapshot=snapshots.get(key)
        if not snapshot:
            results[key]={"status":"MISSING_FEED","markets":[]}
            continue
        if snapshot.get("source_authorized") is not True:
            results[key]={"status":"UNAUTHORIZED_SOURCE","markets":[]}
            continue
        copied={**snapshot,"moneylines":[]}
        for item in snapshot.get("moneylines",[]):
            if not isinstance(item,dict) or item.get("sportsbook","").casefold()!=PROVIDERS[key].casefold():
                continue
            copied["moneylines"].append(item)
        try:
            normalized=normalize(copied)
        except (KeyError,ValueError,TypeError,AttributeError):
            results[key]={"status":"INVALID_SNAPSHOT","markets":[]}
            continue
        results[key]={"status":"IMPORTED","markets":normalized["markets"],
                      "captured_at_utc":normalized["captured_at_utc"]}
        for market in normalized["markets"]:
            if "event_id" not in market or "fighter" not in market or "opponent" not in market:
                continue
            event_key=(market["event_id"],market["fighter"].casefold(),market["opponent"].casefold())
            by_event.setdefault(event_key,{})[key]=market
    comparisons=[]
    for (event_id,fighter,opponent),prices in sorted(by_event.items()):
        if len(prices)!=2:
            comparisons.append({"event_id":event_id,"fighter":fighter,"opponent":opponent,
                                "status":"MISSING_OTHER_BOOK","books":sorted(prices)})
            continue
        dk,fd=prices["draftkings"],prices["fanduel"]
        if dk.get("model_probability")!=fd.get("model_probability"):
            status="MODEL_PROBABILITY_MISMATCH"
        elif "expected_roi_per_unit" not in dk or "expected_roi_per_unit" not in fd:
            status="INCOMPLETE_MARKET"
        else:
            status="COMPARABLE_RESEARCH"
        comparisons.append({"event_id":event_id,"fighter":fighter,"opponent":opponent,
                            "status":status,"preferred_by_estimated_roi":(
                                "DraftKings" if dk["expected_roi_per_unit"]>fd["expected_roi_per_unit"] else
                                "FanDuel" if fd["expected_roi_per_unit"]>dk["expected_roi_per_unit"] else
                                "Tie") if status=="COMPARABLE_RESEARCH" else None,
                            "dk_estimated_roi":dk.get("expected_roi_per_unit"),
                            "fd_estimated_roi":fd.get("expected_roi_per_unit"),
                            "bet_eligible":False})
    return {"schema":1,"sport":"UFC","providers":results,"comparisons":comparisons,
            "bet_eligible":False,"research_only":True,
            "note":"No live feed, account authorization, or bet execution is implied."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--draftkings",required=True)
    p.add_argument("--fanduel",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    report=compare({"draftkings":json.loads(Path(a.draftkings).read_text()),
                    "fanduel":json.loads(Path(a.fanduel).read_text())})
    out=Path(a.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print("DK:",report["providers"]["draftkings"]["status"])
    print("FD:",report["providers"]["fanduel"]["status"])
    print("Comparisons:",len(report["comparisons"]))
if __name__=="__main__": main()
