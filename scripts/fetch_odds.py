#!/usr/bin/env python3
"""Manual, free-quota odds snapshot publisher. API key stays in GitHub Actions secrets."""
import json, os, sys, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

SPORTS={"americanfootball_nfl","americanfootball_ncaaf","basketball_nba","basketball_ncaab","baseball_mlb","icehockey_nhl","soccer_epl","mma_mixed_martial_arts"}
MARKETS={"h2h","spreads","totals"}
PROP_MARKETS={"player_pass_yds","player_pass_tds","player_rush_yds","player_reception_yds","player_receptions","player_anytime_td"}
def validate_rows(rows, sport, now=None):
    """Reject empty or stale NFL moneyline responses before overwriting saved data."""
    if sport != "americanfootball_nfl":
        return True
    now = now or datetime.now(timezone.utc)
    for row in rows:
        if row.get("market") != "h2h" or row.get("bookmaker") not in ("fanduel", "draftkings"):
            continue
        try:
            kickoff = datetime.fromisoformat(row["commence_time"].replace("Z", "+00:00"))
            updated = datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00"))
            if kickoff.tzinfo is None or updated.tzinfo is None:
                continue
            if kickoff <= now or updated > now + timedelta(minutes=2):
                continue
            if now - updated > timedelta(hours=8):
                continue
            if not isinstance(row.get("price"), (int, float)):
                continue
            return True
        except (ValueError, TypeError, AttributeError, KeyError):
            continue
    return False

def main():
    key=os.environ.get("THE_ODDS_API_KEY")
    if not key:
        print("THE_ODDS_API_KEY missing: configure Actions repository secret.")
        return 2
    sport=os.getenv("ODDS_SPORT","americanfootball_nfl")
    markets=os.getenv("ODDS_MARKETS","h2h")
    if sport not in SPORTS or not set(markets.split(",")).issubset(MARKETS):
        print("Unsupported sport or market selection");return 2
    if set(markets.split(",")) & PROP_MARKETS:
        print("Player props require event-level endpoint and separate credit accounting; no unsupported request sent")
        return 2
    params=urllib.parse.urlencode({"apiKey":key,"regions":"us","bookmakers":"fanduel,draftkings","markets":markets,"oddsFormat":"american"})
    req=urllib.request.Request("https://api.the-odds-api.com/v4/sports/"+sport+"/odds?"+params,headers={"User-Agent":"KennysSportsLab/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=30) as response:
            events=json.load(response)
            remaining=response.headers.get("x-requests-remaining")
    except urllib.error.HTTPError as err:
        print("Odds provider returned HTTP",err.code,"(no snapshot published)")
        return 1
    except Exception as err:
        print("Odds provider unavailable:",type(err).__name__)
        return 1
    if not isinstance(events,list):
        print("Unexpected API response");return 1
    rows=[]
    for event in events:
        for book in event.get("bookmakers",[]):
            if book.get("key") not in ("fanduel","draftkings"):continue
            for market in book.get("markets",[]):
                for outcome in market.get("outcomes",[]):
                    rows.append({"event":str(event.get("away_team",""))+" @ "+str(event.get("home_team","")),"event_id":event.get("id"),"commence_time":event.get("commence_time"),"sport":sport,"market":market.get("key"),"description":outcome.get("description"),"player":outcome.get("description"),"selection":outcome.get("name"),"point":outcome.get("point"),"price":outcome.get("price"),"bookmaker":book.get("key"),"updated_at":market.get("last_update") or book.get("last_update")})
    if not validate_rows(rows, sport):
        print("NFL odds response has no fresh pregame DK/FD moneylines; existing snapshot retained")
        return 1
    output={"source":"the-odds-api-v4","status":"ok","sport":sport,"markets_requested":markets.split(","),"fetched_at":datetime.now(timezone.utc).isoformat(),"remaining_credits":remaining,"odds":rows}
    path=Path("feed") / (sport + ".json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if sport != "mma_mixed_martial_arts":
        Path("feed/latest.json").write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Saved",len(rows),"selections. Remaining free credits:",remaining)
    return 0
if __name__=="__main__":sys.exit(main())
