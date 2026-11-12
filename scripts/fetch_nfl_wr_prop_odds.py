"""Fetch authorized NFL player props from existing The Odds API credentials.

Explicitly opt-in with NFL_WR_PROPS_ENABLED=1; limited to a small event budget.
Never overwrite verified snapshots when the provider fails.
"""
import datetime as dt
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request

BASE = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl"
MARKETS = "player_receptions,player_reception_yds,player_anytime_td"
BOOKS = {"fanduel", "draftkings"}

def get_json(url, opener=urllib.request.urlopen):
    with opener(urllib.request.Request(url, headers={"User-Agent":"KennysSportsLab/1.0"}), timeout=30) as response:
        return json.load(response)

def fetch(key, limit=2, get=get_json):
    params = urllib.parse.urlencode({"apiKey":key})
    events = get(BASE + "/events?" + params)
    if not isinstance(events, list):
        raise ValueError("invalid events")
    now = dt.datetime.now(dt.timezone.utc)
    eligible = []
    for event in events:
        try:
            kickoff = dt.datetime.fromisoformat(event["commence_time"].replace("Z", "+00:00"))
            if kickoff > now and kickoff <= now + dt.timedelta(days=7) and event.get("id"):
                eligible.append((kickoff, event))
        except (KeyError, ValueError, TypeError):
            continue
    eligible.sort(key=lambda x:x[0])
    rows = []
    for _, event in eligible[:limit]:
        query = urllib.parse.urlencode({"apiKey":key, "regions":"us", "bookmakers":"fanduel,draftkings", "markets":MARKETS, "oddsFormat":"american"})
        result = get(BASE + "/events/" + urllib.parse.quote(event["id"],safe="") + "/odds?" + query)
        for book in result.get("bookmakers",[]):
            if book.get("key") not in BOOKS:
                continue
            for market in book.get("markets",[]):
                if market.get("key") not in MARKETS.split(","):
                    continue
                for outcome in market.get("outcomes",[]):
                    if not outcome.get("description") or not isinstance(outcome.get("price"),(int,float)):
                        continue
                    rows.append({"event_id":event["id"],"commence_time":event["commence_time"],"player_name":outcome["description"],"market":market["key"],"side":outcome.get("name"),"line":(0.5 if market["key"]=="player_anytime_td" and outcome.get("point") is None else outcome.get("point")),"american_odds":outcome["price"],"book":book["key"],"verified_at":market.get("last_update") or book.get("last_update"),"source":"the-odds-api-v4"})
    return rows

def main():
    if os.getenv("NFL_WR_PROPS_ENABLED") != "1":
        print("NFL WR prop fetch disabled; avoiding unapproved API credit use")
        return
    key = os.getenv("THE_ODDS_API_KEY")
    if not key:
        raise SystemExit("THE_ODDS_API_KEY unavailable")
    limit = min(4, max(1,int(os.getenv("NFL_WR_PROP_EVENT_LIMIT","2"))))
    rows = fetch(key,limit)
    if not rows:
        raise SystemExit("No valid player prop quotes; existing snapshot retained")
    path = Path("feed/nfl_wr_prop_odds.json")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({"fetched_at":dt.datetime.now(dt.timezone.utc).isoformat(),"odds":rows},indent=2)+"\n")
    print("Published",len(rows),"NFL player prop quotes from",limit,"events")

if __name__ == "__main__":
    main()
