#!/usr/bin/env python3
"""Normalize existing Odds API snapshots into exact-contract sportsbook quotes.
A quote is verified only when provider metadata is valid and fresh. No model estimates.
"""
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from scripts.build_market_edges import timestamp

SOURCES={"NBA":"basketball_nba","NHL":"icehockey_nhl","NFL":"americanfootball_nfl","NCAAB":"basketball_ncaab"}
MARKETS={"h2h":"ML","spreads":"SPREAD","totals":"TOTAL"}
def normalize(feeds,now=None):
    now=now or datetime.now(timezone.utc)
    quotes=[]
    counts={}
    for sport,feed in feeds.items():
        if sport not in SOURCES or not isinstance(feed,dict) or feed.get("status")!="ok" or feed.get("sport")!=SOURCES[sport] or feed.get("source")!="the-odds-api-v4":
            counts[sport]=0
            continue
        fetched=timestamp(feed.get("fetched_at"))
        if not fetched or not 0<=(now-fetched).total_seconds()<=900:
            counts[sport]=0
            continue
        count=0
        for r in feed.get("odds",[]):
            if not isinstance(r,dict) or r.get("market") not in MARKETS or r.get("bookmaker") not in ("fanduel","draftkings"):
                continue
            stamp=timestamp(r.get("updated_at"))
            start=timestamp(r.get("commence_time"))
            price=r.get("price")
            if not stamp or not start or not 0<=(now-stamp).total_seconds()<=900 or start<=now:
                continue
            if type(price) not in (int,float) or not math.isfinite(price) or abs(price)<100:
                continue
            point=r.get("point")
            if r["market"]!="h2h" and (type(point) not in (int,float) or not math.isfinite(point)):
                continue
            event=r.get("event")
            selection=r.get("selection")
            eid=r.get("event_id")
            if not all(isinstance(v,str) and v.strip() for v in (event,selection,eid)):
                continue
            quotes.append({"sport":sport,"event_id":eid,"market":MARKETS[r["market"]],"selection_id":selection.strip() if r["market"]!="totals" else selection.strip().lower(),"point":point if r["market"]!="h2h" else None,"odds":price,"source":r["bookmaker"],"price_verified":True,"odds_timestamp":stamp.isoformat(),"start_time":start.isoformat()})
            count+=1
        counts[sport]=count
    return {"generated_at":now.isoformat(),"status":"VERIFIED" if quotes else "UNAVAILABLE","quotes":quotes,"counts":counts}

def main():
    feeds={}
    for sport,slug in SOURCES.items():
        path=Path("feed")/(slug+".json")
        if path.exists():
            try:feeds[sport]=json.loads(path.read_text())
            except (OSError,ValueError):feeds[sport]={}
    result=normalize(feeds)
    out=Path("data/verified_sportsbook_quotes.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
    print(result["status"],result["counts"])
if __name__=="__main__":main()
