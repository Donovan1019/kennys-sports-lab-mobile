#!/usr/bin/env python3
"""Fetch NBA DK/FD player points props from SportsGameOdds v2, fail closed."""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BOOKS = ("draftkings", "fanduel")
OUTPUT = Path("feed/nba_props.json")

def parse_time(value):
    try:
        d = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return d if d.tzinfo else None
    except (ValueError, TypeError):
        return None

def price(value):
    try:
        n = int(str(value).replace("+", ""))
        return n if n >= 100 or n <= -100 else None
    except (ValueError, TypeError):
        return None

def player_name(event, entity):
    player = (event.get("players") or {}).get(entity) or {}
    names = player.get("names") or {}
    return names.get("display") or names.get("long") or player.get("name")

def normalize(payload, now):
    if payload.get("success") is not True or not isinstance(payload.get("data"), list):
        raise ValueError("invalid SportsGameOdds response")
    rows = []
    for event in payload["data"]:
        if event.get("leagueID") != "NBA":
            continue
        status = event.get("status") or {}
        start = parse_time(status.get("startsAt"))
        if not start or not now < start <= now + timedelta(days=3) or any(status.get(k) for k in ("started", "ended", "cancelled", "completed")):
            continue
        event_id = event.get("eventID")
        if not event_id:
            continue
        for odd in (event.get("odds") or {}).values():
            if not isinstance(odd, dict) or odd.get("statID") != "points" or odd.get("periodID") != "game" or odd.get("betTypeID") != "ou" or odd.get("sideID") not in ("over", "under"):
                continue
            entity = odd.get("statEntityID")
            if not entity or entity in ("all", "home", "away"):
                continue
            name = player_name(event, entity)
            if not name:
                continue
            for book in BOOKS:
                q = (odd.get("byBookmaker") or {}).get(book) or {}
                for quote in [q] + list(q.get("altLines") or []):
                    if not isinstance(quote, dict) or quote.get("available") is not True:
                        continue
                    updated = parse_time(quote.get("lastUpdatedAt") or q.get("lastUpdatedAt"))
                    if not updated or not now-timedelta(hours=2) <= updated <= now+timedelta(minutes=5):
                        continue
                    try:
                        point = float(quote.get("overUnder"))
                    except (ValueError, TypeError):
                        continue
                    p = price(quote.get("odds"))
                    if p is None or not 0 < point < 100:
                        continue
                    rows.append({"event_id": str(event_id), "event": str(event_id), "commence_time": start.isoformat(), "market": "player_points_alternate" if quote is not q else "player_points", "player": name, "selection": odd["sideID"].title(), "point": point, "price": p, "bookmaker": book, "updated_at": updated.isoformat()})
    return rows

def main():
    key = os.getenv("SPORTSGAMEODDS_API_KEY")
    if not key:
        print("SPORTSGAMEODDS_API_KEY missing; existing feed retained")
        return 2
    now = datetime.now(timezone.utc)
    query = urllib.parse.urlencode({"leagueID": "NBA", "type": "match", "started": "false", "oddsAvailable": "true", "bookmakerID": ",".join(BOOKS), "startsAfter": now.isoformat(), "startsBefore": (now+timedelta(days=3)).isoformat(), "includeAltLines": "true", "limit": "10"})
    request = urllib.request.Request("https://api.sportsgameodds.com/v2/events?" + query, headers={"x-api-key": key, "User-Agent": "KennysSportsLab/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            payload = json.load(response)
        rows = normalize(payload, now)
    except Exception as exc:
        print("SportsGameOdds NBA props failed:", type(exc).__name__, str(exc)[:120])
        return 1
    if not rows:
        print("SportsGameOdds returned no available fresh DK/FD player points props; existing feed retained")
        return 1
    data = {"sport": "basketball_nba", "source": "sportsgameodds-v2-player-props", "fetched_at": now.isoformat(), "markets_requested": ["player_points", "player_points_alternate"], "books": list(BOOKS), "odds": rows}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    tmp.replace(OUTPUT)
    print("Published", len(rows), "SportsGameOdds player points quotes")
    return 0

if __name__ == "__main__":
    sys.exit(main())
