#!/usr/bin/env python3
"""Opt-in, capped NFL event-level player-prop snapshot. Never runs on a timer.
Requires explicit MAX_EVENTS (1-3); API usage varies by bookmaker/market/event.
"""
import json, os, sys, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

SPORT="americanfootball_nfl"
MARKETS=("player_pass_yds","player_pass_tds","player_rush_yds",
         "player_reception_yds","player_receptions","player_anytime_td")
BOOKS=("fanduel","draftkings")
BASE="https://api.the-odds-api.com/v4/sports/"+SPORT

def request_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"KennysSportsLab/1.0"})
    with urllib.request.urlopen(req,timeout=40) as response:
        return json.load(response),response.headers.get("x-requests-remaining")

def extract(event, data):
    rows=[]
    for book in data.get("bookmakers",[]):
        if book.get("key") not in BOOKS:continue
        for market in book.get("markets",[]):
            if market.get("key") not in MARKETS:continue
            for outcome in market.get("outcomes",[]):
                price=outcome.get("price")
                if not isinstance(price,(int,float)) or -100<price<100:continue
                rows.append({
                    "event_id":event["id"],"event":event["away_team"]+" @ "+event["home_team"],
                    "commence_time":event.get("commence_time"),"market":market["key"],
                    "player":outcome.get("description"),"selection":outcome.get("name"),
                    "point":outcome.get("point"),"price":price,"bookmaker":book["key"],
                    "updated_at":market.get("last_update") or book.get("last_update")
                })
    return rows

def main():
    key=os.environ.get("THE_ODDS_API_KEY")
    if not key:print("Missing secret");return 2
    try:limit=int(os.environ.get("MAX_EVENTS","0"))
    except ValueError:return 2
    if not 1<=limit<=20:
        print("Choose MAX_EVENTS between 1 and 20 explicitly; no requests made");return 2
    query=lambda d:urllib.parse.urlencode(d)
    common={"apiKey":key,"bookmakers":",".join(BOOKS),"oddsFormat":"american"}
    try:
        events,remaining=request_json(BASE+"/events?"+query({"apiKey":key}))
        if not isinstance(events,list):raise ValueError("Unexpected events response")
        events=sorted((e for e in events if e.get("id") and e.get("commence_time") and e.get("away_team") and e.get("home_team")),key=lambda e:e["commence_time"])
        now=datetime.now(timezone.utc)
        upcoming=[]
        for e in events:
            try:
                kickoff=datetime.fromisoformat(e["commence_time"].replace("Z","+00:00"))
                if kickoff>now:upcoming.append(e)
            except (ValueError,TypeError):pass
        print("Provider events",len(events),"eligible future events",len(upcoming))
        events=upcoming
        target_date=os.environ.get("TARGET_DATE")
        if target_date:
            datetime.strptime(target_date,"%Y-%m-%d")
            events=[e for e in events if datetime.fromisoformat(e["commence_time"].replace("Z","+00:00")).astimezone(ZoneInfo("America/New_York")).date().isoformat()==target_date]
            print("Target date",target_date,"games",len(events))
        events=events[:limit]
        if not events:print("No upcoming events; no snapshot overwritten");return 1
        rows=[];errors=[]
        for event in events:
            try:
                payload,remaining=request_json(BASE+"/events/"+urllib.parse.quote(event["id"],safe="")+"/odds?"+query({**common,"markets":",".join(MARKETS)}))
                rows.extend(extract(event,payload))
                print(event["id"],"selections",len(rows),"credits remaining",remaining)
            except (urllib.error.HTTPError,urllib.error.URLError,ValueError) as exc:
                errors.append({"event_id":event["id"],"error":type(exc).__name__})
                print("Event unavailable",event["id"],type(exc).__name__)
        if not rows:print("No verified prop prices returned; old feed preserved");return 1
        output={"source":"the-odds-api-v4-event-props","sport":SPORT,
                "fetched_at":datetime.now(timezone.utc).isoformat(),
                "markets_requested":list(MARKETS),"books":list(BOOKS),
                "events_requested":len(events),"errors":errors,
                "remaining_credits":remaining,"odds":rows}
        path=Path("feed/nfl_props.json");path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(output,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
        print("Saved",len(rows),"verified prop prices")
        return 0
    except (urllib.error.HTTPError,urllib.error.URLError,ValueError) as exc:
        print("Provider unavailable",type(exc).__name__);return 1
if __name__=="__main__":sys.exit(main())
