#!/usr/bin/env python3
"""Refresh NBA event-level player props using the existing Odds API secret."""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = "https://api.the-odds-api.com/v4"
SPORT = "basketball_nba"
MARKETS = ("player_points_rebounds_assists", "player_points", "player_rebounds", "player_assists")
BOOKS = ("draftkings", "fanduel")
OUTPUT = Path("feed/nba_props.json")


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "KennysSportsLab/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response), response.headers.get("x-requests-remaining")


def iso(value):
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return result if result.tzinfo else None
    except (ValueError, TypeError):
        return None


def main():
    key = os.environ.get("THE_ODDS_API_KEY")
    if not key:
        print("THE_ODDS_API_KEY not configured; existing feed retained")
        return 2
    now = datetime.now(timezone.utc)
    params = urllib.parse.urlencode({"apiKey": key})
    try:
        events, credits = fetch(f"{BASE}/sports/{SPORT}/events?{params}")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
        print("Could not retrieve NBA events:", str(exc)[:180])
        return 1
    if not isinstance(events, list):
        print("Invalid events response; existing feed retained")
        return 1
    upcoming = [event for event in events if isinstance(event, dict) and
                (start := iso(event.get("commence_time"))) and now < start <= now + timedelta(days=3)]
    upcoming.sort(key=lambda event: event["commence_time"])
    limit = min(int(os.getenv("NBA_PROPS_MAX_EVENTS", "12")), 20)
    upcoming = upcoming[:limit]
    if not upcoming:
        print("No upcoming NBA events; existing feed retained")
        return 1
    rows, errors, successes = [], [], 0
    for event in upcoming:
        event_id = event.get("id")
        if not event_id:
            continue
        query = urllib.parse.urlencode({
            "apiKey": key, "regions": "us", "bookmakers": ",".join(BOOKS),
            "markets": ",".join(MARKETS), "oddsFormat": "american"
        })
        try:
            result, credits = fetch(f"{BASE}/sports/{SPORT}/events/{urllib.parse.quote(str(event_id), safe='')}/odds?{query}")
            successes += 1
        except urllib.error.HTTPError as exc:
            errors.append({"event_id": event_id, "http_status": exc.code})
            continue
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            errors.append({"event_id": event_id, "error": type(exc).__name__})
            continue
        for book in result.get("bookmakers", []):
            if book.get("key") not in BOOKS:
                continue
            for market in book.get("markets", []):
                market_key = market.get("key")
                if market_key not in MARKETS:
                    continue
                updated = market.get("last_update") or book.get("last_update")
                if not (stamp := iso(updated)) or not now - timedelta(hours=8) <= stamp <= now + timedelta(minutes=5):
                    continue
                for outcome in market.get("outcomes", []):
                    point, price = outcome.get("point"), outcome.get("price")
                    if (not isinstance(point, (int, float)) or isinstance(point, bool) or
                        not isinstance(price, (int, float)) or isinstance(price, bool) or
                        outcome.get("name") not in ("Over", "Under") or not outcome.get("description")):
                        continue
                    rows.append({
                        "event_id": event_id,
                        "event": str(event.get("away_team", "")) + " @ " + str(event.get("home_team", "")),
                        "commence_time": event.get("commence_time"),
                        "market": market_key,
                        "player": outcome["description"],
                        "selection": outcome["name"],
                        "point": point,
                        "price": price,
                        "bookmaker": book["key"],
                        "updated_at": updated,
                    })
        time.sleep(0.12)
    pra = [row for row in rows if row["market"] == "player_points_rebounds_assists"]
    if not successes or not pra:
        print(f"No fresh PRA quotes: successful events={successes}, rows={len(rows)}; existing feed retained")
        return 1
    output = {
        "sport": SPORT, "source": "the-odds-api-v4-event-props",
        "fetched_at": now.isoformat(), "markets_requested": list(MARKETS),
        "events_requested": len(upcoming), "books": list(BOOKS),
        "remaining_credits": credits, "errors": errors, "odds": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUTPUT.with_suffix(".json.tmp")
    temp.write_text(json.dumps(output, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    temp.replace(OUTPUT)
    print(f"Published {len(rows)} fresh player prop quotes ({len(pra)} PRA), {successes} events; credits remaining: {credits}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
