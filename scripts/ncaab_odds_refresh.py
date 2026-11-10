#!/usr/bin/env python3
"""Fetch verified NCAAB h2h/spreads/totals odds. Never publish stale or empty responses."""
import datetime as dt
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request

OUT=Path("data/ncaab_odds.json")
def main():
    key=os.getenv("ODDS_API_KEY") or os.getenv("THE_ODDS_API_KEY")
    if not key:
        raise RuntimeError("ODDS_API_KEY or THE_ODDS_API_KEY secret missing; old cache preserved")
    url="https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds/?"+urllib.parse.urlencode({
        "apiKey":key,"regions":"us,us2","markets":"h2h,spreads,totals","oddsFormat":"american","dateFormat":"iso"})
    req=urllib.request.Request(url,headers={"User-Agent":"KennysSportsLab/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=40) as response:
        data=json.load(response)
        remaining=response.headers.get("x-requests-remaining")
    if not isinstance(data,list) or not data:
        raise RuntimeError("Odds API returned no games; old cache preserved")
    now=dt.datetime.now(dt.timezone.utc)
    clean=[]
    for event in data:
        if not isinstance(event,dict) or not all(event.get(k) for k in ("id","commence_time","home_team","away_team")):
            continue
        try: start=dt.datetime.fromisoformat(event["commence_time"].replace("Z","+00:00"))
        except ValueError: continue
        if start<=now: continue
        books=[]
        for book in event.get("bookmakers") or []:
            try: updated=dt.datetime.fromisoformat(book["last_update"].replace("Z","+00:00"))
            except (KeyError,ValueError,TypeError): continue
            if updated>now+dt.timedelta(minutes=5) or now-updated>dt.timedelta(hours=6):continue
            markets=[]
            for market in book.get("markets") or []:
                if market.get("key") not in ("h2h","spreads","totals"):continue
                outcomes=[o for o in market.get("outcomes") or [] if isinstance(o.get("price"),(int,float)) and o["price"]!=0]
                if len(outcomes)>=2:markets.append({"key":market["key"],"outcomes":outcomes})
            if markets:books.append({"key":book.get("key"),"title":book.get("title"),"last_update":book["last_update"],"markets":markets})
        if books:clean.append({"id":event["id"],"commence_time":event["commence_time"],"home_team":event["home_team"],"away_team":event["away_team"],"bookmakers":books})
    if not clean:
        raise RuntimeError("No upcoming games with fresh valid bookmaker prices; old cache preserved")
    output={"sport":"basketball_ncaab","fetched_at":now.isoformat(),"remaining_credits":int(remaining) if remaining and remaining.isdigit() else None,"events":clean}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(output,separators=(",",":"))+"\n")
    print("Published",len(clean),"upcoming games; credits remaining:",output["remaining_credits"])
if __name__=="__main__":main()
