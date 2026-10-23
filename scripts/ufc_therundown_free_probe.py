#!/usr/bin/env python3
"""Probe TheRundown's free DK/FD UFC coverage without guessing catalog IDs.

Requires user-owned THERUNDOWN_API_KEY. Never logs the key or publishes
unverified prices. The catalog calls are free according to provider docs.
"""
import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE="https://therundown.io/api/v2"
def request_catalog(path,key,opener=urlopen):
    if path not in ("sports","affiliates","markets"):
        raise ValueError("Only allowlisted free reference catalogs")
    if not key: raise ValueError("THERUNDOWN_API_KEY not configured")
    req=Request(BASE+"/"+path,headers={"X-TheRundown-Key":key,"Accept":"application/json"})
    with opener(req,timeout=20) as response:
        return json.loads(response.read())

def catalog_report(sports,affiliates,markets):
    def flatten(x):
        if isinstance(x,list): return x
        if isinstance(x,dict):
            for k in ("data","sports","affiliates","markets","results"):
                if isinstance(x.get(k),list): return x[k]
        return []
    def matching(rows,words):
        return [r for r in rows if isinstance(r,dict) and
                any(w in json.dumps(r,ensure_ascii=True).lower() for w in words)]
    return {"schema":1,"provider":"TheRundown","research_only":True,
            "sport_candidates":matching(flatten(sports),("ufc","mma","mixed martial")),
            "book_candidates":matching(flatten(affiliates),("draftkings","fanduel")),
            "market_candidates":matching(flatten(markets),("moneyline","head to head","h2h")),
            "prices_fetched":False,"live_connected":False,"bet_eligible":False,
            "next_step":"Confirm UFC sport ID, DK/FD affiliate IDs and moneyline market ID; then test a bounded dated odds response using a free key."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="/tmp/ufc_therundown_catalog.json")
    p.add_argument("--fixture-dir",help="Offline fixtures: sports.json, affiliates.json, markets.json")
    a=p.parse_args()
    if a.fixture_dir:
        folder=Path(a.fixture_dir)
        catalogs=[json.loads((folder/(x+".json")).read_text()) for x in ("sports","affiliates","markets")]
    else:
        key=os.environ.get("THERUNDOWN_API_KEY")
        if not key: raise SystemExit("UNAVAILABLE: THERUNDOWN_API_KEY is not set; no requests made.")
        try: catalogs=[request_catalog(x,key) for x in ("sports","affiliates","markets")]
        except (HTTPError,URLError,TimeoutError,ValueError) as e:
            raise SystemExit("Provider catalog request failed: "+type(e).__name__)
    result=catalog_report(*catalogs)
    Path(a.output).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
