#!/usr/bin/env python3
"""Refresh UFC moneyline quotes from The Odds API. Never invent or reuse stale odds."""
import json, os, urllib.request
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"feed/mma_mixed_martial_arts.json"
def convert(events, now):
    rows=[]
    for event in events:
        if not isinstance(event,dict) or not event.get("id") or not event.get("commence_time"): continue
        for book in event.get("bookmakers",[]):
            if book.get("key") not in ("draftkings","fanduel"):continue
            for market in book.get("markets",[]):
                if market.get("key")!="h2h":continue
                updated=market.get("last_update") or book.get("last_update")
                for outcome in market.get("outcomes",[]):
                    if isinstance(outcome.get("price"),(int,float)) and outcome.get("name"):
                        rows.append({"event":event.get("away_team","")+" @ "+event.get("home_team",""),"event_id":event["id"],"commence_time":event["commence_time"],"sport":"mma_mixed_martial_arts","market":"h2h","description":None,"player":None,"selection":outcome["name"],"point":None,"price":outcome["price"],"bookmaker":book["key"],"updated_at":updated})
    return {"source":"the-odds-api-v4","status":"ok","sport":"mma_mixed_martial_arts","markets_requested":["h2h"],"fetched_at":now.isoformat(),"odds":rows}
def main():
    key=os.getenv("ODDS_API_KEY") or os.getenv("THE_ODDS_API_KEY")
    if not key: raise SystemExit("Missing ODDS_API_KEY/THE_ODDS_API_KEY secret; existing feed unchanged")
    url="https://api.the-odds-api.com/v4/sports/mma_mixed_martial_arts/odds?regions=us&markets=h2h&oddsFormat=american&apiKey="+key
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"KSL-UFC-Odds-Refresh/1.0"}),timeout=25) as response:
        events=json.load(response)
    if not isinstance(events,list):raise ValueError("Unexpected odds API response; existing feed unchanged")
    data=convert(events,datetime.now(timezone.utc))
    # Empty legitimate API response is explicit, not old prices disguised as current.
    DEST.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")
    print("UFC odds: %d quotes across %d events"%(len(data["odds"]),len(events)))
if __name__=="__main__":main()
