#!/usr/bin/env python3
"""Authorized TheOddsAPI UFC odds ingest for DK/FD; no key stored in repo.

Uses documented /odds/ endpoint. Requires ODDS_API_KEY secret and MMA access.
Does not infer independent model probabilities or claim betting eligibility.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ENDPOINT="https://api.theoddsapi.com/odds/"
BOOKS={"draftkings":"DraftKings","fanduel":"FanDuel"}

def parse_time(s):
    x=dt.datetime.fromisoformat(s.replace("Z","+00:00"))
    if x.utcoffset() is None: raise ValueError("Timestamp must be offset aware")
    return x

def convert(payload, captured_at):
    if not isinstance(payload,dict) or payload.get("success") is not True:
        raise ValueError("Unexpected provider response")
    events=payload.get("data")
    if not isinstance(events,list): raise ValueError("No events array")
    outputs={key:{"schema":1,"sport":"UFC","source":"theoddsapi.com",
                  "source_authorized":True,"captured_at_utc":captured_at,
                  "moneylines":[]} for key in BOOKS}
    for event in events:
        if not isinstance(event,dict) or event.get("sport") not in ("mma_mixed_martial_arts","mma"):
            continue
        fighters=(event.get("home_team"),event.get("away_team"))
        if any(not isinstance(x,str) or not x.strip() for x in fighters) or fighters[0]==fighters[1]:
            continue
        event_id=event.get("event_id")
        start=event.get("start_time")
        if not isinstance(event_id,str) or not event_id or not isinstance(start,str):
            continue
        try:
            if parse_time(start)<=parse_time(captured_at): continue
        except ValueError: continue
        for book in event.get("books",[]):
            key=book.get("book")
            if key not in BOOKS or book.get("market")!="h2h": continue
            outcomes=book.get("outcomes",[])
            if not isinstance(outcomes,list) or len(outcomes)!=2: continue
            prices={x.get("name"):x.get("price") for x in outcomes if isinstance(x,dict)}
            if set(prices)!=set(fighters): continue
            try:
                updated=parse_time(book["updated_at"])
                if updated>parse_time(captured_at) or updated>=parse_time(start):
                    continue
            except (ValueError,KeyError,TypeError,AttributeError): continue
            for fighter,opponent in (fighters,tuple(reversed(fighters))):
                outputs[key]["moneylines"].append({
                    "event_id":event_id,"fighter":fighter,"opponent":opponent,
                    "fighter_odds":prices[fighter],"opponent_odds":prices[opponent],
                    "event_start_utc":start,"sportsbook":BOOKS[key],
                    "book_updated_at_utc":book["updated_at"],
                    "source_verified":False,"fighters_verified":False,
                    "model_calibrated":False,"odds_executable":False})
    return outputs

def fetch(api_key):
    if not api_key: raise ValueError("ODDS_API_KEY secret is required")
    query=urlencode({"sport_key":"mma_mixed_martial_arts","markets":"h2h",
                     "bookmakers":"draftkings,fanduel","oddsFormat":"american"})
    request=Request(ENDPOINT+"?"+query,headers={"x-api-key":api_key,"User-Agent":"KennysSportsLab/1.0"})
    with urlopen(request,timeout=25) as response:
        return json.loads(response.read())

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",default="feed/ufc_books")
    p.add_argument("--input-json",help="Use authorized downloaded provider response instead of live API")
    args=p.parse_args()
    payload=json.loads(Path(args.input_json).read_text()) if args.input_json else fetch(os.environ.get("ODDS_API_KEY"))
    captured=dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00","Z")
    results=convert(payload,captured)
    folder=Path(args.output_dir)
    folder.mkdir(parents=True,exist_ok=True)
    for key,data in results.items():
        (folder/(key+".json")).write_text(json.dumps(data,indent=2)+"\n")
        print(key,len(data["moneylines"]),"fighter-side quotes; research only")
if __name__=="__main__": main()
