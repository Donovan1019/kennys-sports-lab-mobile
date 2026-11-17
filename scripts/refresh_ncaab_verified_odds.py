#!/usr/bin/env python3
"""Refresh NCAA basketball sportsbook quotes without ever publishing stale/fabricated prices."""
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

DEST = pathlib.Path("data/ncaab_odds.json")
URL = "https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds/"
def main():
    key = os.getenv("ODDS_API_KEY") or os.getenv("THE_ODDS_API_KEY")
    if not key:
        raise RuntimeError("Missing ODDS_API_KEY / THE_ODDS_API_KEY Actions secret")
    query = urllib.parse.urlencode({"apiKey":key,"regions":"us,us2","markets":"h2h,spreads,totals","oddsFormat":"american","dateFormat":"iso"})
    req = urllib.request.Request(URL+"?"+query,headers={"User-Agent":"KennysSportsLab/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=35) as response:
            events=json.load(response)
            remaining=response.headers.get("x-requests-remaining")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Odds provider HTTP {exc.code}; previous snapshot preserved") from None
    if not isinstance(events,list):
        raise RuntimeError("Odds provider returned invalid events; previous snapshot preserved")
    now=dt.datetime.now(dt.timezone.utc)
    valid=[]
    for event in events:
        if not isinstance(event,dict) or not all(event.get(k) for k in ("id","home_team","away_team","commence_time")):
            continue
        try:
            tip=dt.datetime.fromisoformat(event["commence_time"].replace("Z","+00:00"))
        except (ValueError,TypeError):
            continue
        if tip < now-dt.timedelta(hours=5):
            continue
        books=[]
        for book in event.get("bookmakers",[]):
            markets=[m for m in book.get("markets",[]) if m.get("key") in ("h2h","spreads","totals") and len(m.get("outcomes",[]))>=2]
            try:
                updated=dt.datetime.fromisoformat(book["last_update"].replace("Z","+00:00"))
            except (KeyError,ValueError,TypeError):
                continue
            if updated < now-dt.timedelta(hours=6) or updated > now+dt.timedelta(minutes=10):
                continue
            if markets:
                books.append({**book,"markets":markets})
        if books:
            valid.append({**event,"bookmakers":books})
    if not valid:
        raise RuntimeError("No fresh NCAA markets returned; previous snapshot preserved")
    payload={"sport":"basketball_ncaab","fetched_at":now.isoformat(),"remaining_credits":int(remaining) if remaining and remaining.isdigit() else None,"events":valid}
    DEST.parent.mkdir(parents=True,exist_ok=True)
    tmp=DEST.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload,separators=(",",":"))+"\n",encoding="utf-8")
    tmp.replace(DEST)
    print(f"Validated {len(valid)} NCAA games with fresh sportsbook markets; remaining credits: {remaining or 'unknown'}")
if __name__=="__main__":
    try: main()
    except Exception as exc:
        print(f"NCAAB odds refresh failed: {exc}",file=sys.stderr)
        sys.exit(1)
