#!/usr/bin/env python3
"""Refresh NFL core game markets using a single credit-limited Odds API request.
No synthetic prices; never overwrite a valid snapshot with an empty response.
"""
import json, os, sys, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

SPORT = "americanfootball_nfl"
MARKETS = ("h2h", "spreads", "totals")
BOOKS = ("draftkings", "fanduel")
OUT = Path("feed/nfl_sgp_core_markets.json")

def main():
    key = os.getenv("THE_ODDS_API_KEY")
    if not key:
        print("THE_ODDS_API_KEY missing; no requests made")
        return 2
    params = urllib.parse.urlencode({
        "apiKey": key, "regions": "us", "bookmakers": ",".join(BOOKS),
        "markets": ",".join(MARKETS), "oddsFormat": "american"
    })
    url = "https://api.the-odds-api.com/v4/sports/" + SPORT + "/odds/?" + params
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":"KennysSportsLab/1.0"}), timeout=40) as response:
            data = json.load(response)
            remaining = response.headers.get("x-requests-remaining")
        if not isinstance(data, list):
            raise ValueError("Invalid provider event list")
        now = datetime.now(timezone.utc)
        rows = []
        for event in data:
            try:
                kickoff = datetime.fromisoformat(event["commence_time"].replace("Z","+00:00"))
                if kickoff.tzinfo is None or kickoff <= now:
                    continue
                event_id = event["id"]
                matchup = event["away_team"] + " @ " + event["home_team"]
            except (KeyError, TypeError, ValueError, AttributeError):
                continue
            for book in event.get("bookmakers", []):
                if book.get("key") not in BOOKS:
                    continue
                for market in book.get("markets", []):
                    if market.get("key") not in MARKETS:
                        continue
                    for outcome in market.get("outcomes", []):
                        price = outcome.get("price")
                        if not isinstance(price, (int, float)) or isinstance(price, bool) or -100 < price < 100:
                            continue
                        rows.append({
                            "event_id": event_id, "event": matchup,
                            "commence_time": event["commence_time"],
                            "market": market["key"], "team": outcome.get("name"),
                            "selection": outcome.get("name"), "point": outcome.get("point"),
                            "price": price, "bookmaker": book["key"],
                            "updated_at": market.get("last_update") or book.get("last_update")
                        })
        if not rows:
            print("No future DK/FD core market prices; prior snapshot preserved")
            return 1
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(json.dumps({
            "source":"the-odds-api-v4-core-markets","sport":SPORT,
            "fetched_at":datetime.now(timezone.utc).isoformat(),
            "markets_requested":list(MARKETS),"books":list(BOOKS),
            "remaining_credits":remaining,"odds":rows
        },separators=(",",":"))+"\n", encoding="utf-8")
        print("Saved",len(rows),"real core market prices; remaining credits",remaining)
        return 0
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError, OSError) as exc:
        print("Provider unavailable; prior snapshot preserved",type(exc).__name__)
        return 1

if __name__ == "__main__":
    sys.exit(main())
