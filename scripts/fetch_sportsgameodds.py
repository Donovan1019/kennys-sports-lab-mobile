#!/usr/bin/env python3
"""SportsGameOdds v2 -> Kenny's canonical pregame DK/FD odds feed.

One page per invocation to conserve event-object credits. Fail closed on absent
or stale quotes; never use consensus/fair odds as sportsbook prices.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fetch_odds import fresh_rows, upcoming_rows, validate_rows

LEAGUES = {
    "americanfootball_nfl": "NFL",
    "americanfootball_ncaaf": "NCAAF",
    "basketball_nba": "NBA",
    "basketball_ncaab": "NCAAB",
    "baseball_mlb": "MLB",
    "icehockey_nhl": "NHL",
}
BOOKS = ("draftkings", "fanduel")


def american(value):
    try:
        number = int(str(value).replace("+", "").strip())
    except (TypeError, ValueError):
        return None
    return number if (100 <= number < 100000 or -100000 < number <= -100) else None


def team_name(event, side):
    obj = event.get("teams", {}).get(side, {})
    if not isinstance(obj, dict):
        return None
    names = obj.get("names") or {}
    return names.get("long") or names.get("medium") or obj.get("teamID")


def normalize(payload, sport, now=None):
    now = now or datetime.now(timezone.utc)
    if not isinstance(payload, dict) or payload.get("success") is not True or not isinstance(payload.get("data"), list):
        raise ValueError("Invalid SportsGameOdds response")
    rows = []
    for event in payload["data"]:
        if not isinstance(event, dict) or event.get("leagueID") != LEAGUES[sport]:
            continue
        status = event.get("status") or {}
        if status.get("started") or status.get("ended") or status.get("cancelled") or status.get("completed"):
            continue
        event_id = event.get("eventID")
        away, home = team_name(event, "away"), team_name(event, "home")
        kickoff = status.get("startsAt")
        if not all((event_id, away, home, kickoff)):
            continue
        for odd in (event.get("odds") or {}).values():
            if not isinstance(odd, dict) or odd.get("periodID") != "game" or odd.get("statID") != "points":
                continue
            bet_type, side = odd.get("betTypeID"), odd.get("sideID")
            if bet_type == "ml" and side in ("home", "away"):
                market, selection, point_field = "h2h", home if side == "home" else away, None
            elif bet_type == "sp" and side in ("home", "away"):
                market, selection, point_field = "spreads", home if side == "home" else away, "spread"
            elif bet_type == "ou" and side in ("over", "under") and odd.get("statEntityID") == "all":
                market, selection, point_field = "totals", side.title(), "overUnder"
            else:
                continue
            for book in BOOKS:
                quote = (odd.get("byBookmaker") or {}).get(book)
                if not isinstance(quote, dict) or quote.get("available") is not True:
                    continue
                price = american(quote.get("odds"))
                if price is None:
                    continue
                point = None
                if point_field:
                    try:
                        point = float(quote[point_field])
                    except (TypeError, ValueError, KeyError):
                        continue
                    if not -10000 < point < 10000:
                        continue
                rows.append({
                    "event": away + " @ " + home, "event_id": str(event_id),
                    "commence_time": kickoff, "sport": sport, "market": market,
                    "description": None, "player": None, "selection": selection,
                    "point": point, "price": price, "bookmaker": book,
                    "updated_at": quote.get("lastUpdatedAt"),
                })
    rows = fresh_rows(upcoming_rows(rows, now), now)
    return rows


def main():
    key = os.getenv("SPORTSGAMEODDS_API_KEY")
    sport = os.getenv("ODDS_SPORT", "basketball_nba")
    requested = set(os.getenv("ODDS_MARKETS", "h2h").split(","))
    if not key or sport not in LEAGUES or not requested or not requested <= {"h2h", "spreads", "totals"}:
        print("SportsGameOdds: missing key, unsupported league or markets")
        return 2
    now = datetime.now(timezone.utc)
    params = urllib.parse.urlencode({
        "leagueID": LEAGUES[sport], "type": "match", "started": "false",
        "oddsAvailable": "true", "bookmakerID": ",".join(BOOKS),
        "startsAfter": now.isoformat(), "startsBefore": (now + timedelta(days=7)).isoformat(),
        "limit": "100", "includeAltLines": "false",
    })
    req = urllib.request.Request(
        "https://api.sportsgameodds.com/v2/events?" + params,
        headers={"x-api-key": key, "User-Agent": "KennysSportsLab/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        print("SportsGameOdds HTTP", error.code, "- existing snapshot retained")
        return 1
    except (OSError, ValueError) as error:
        print("SportsGameOdds request failed:", type(error).__name__)
        return 1
    try:
        rows = [row for row in normalize(payload, sport, now) if row["market"] in requested]
    except (ValueError, TypeError, KeyError) as error:
        print("SportsGameOdds normalization rejected:", type(error).__name__)
        return 1
    if not rows or not validate_rows(rows, sport, now):
        print("SportsGameOdds: no eligible fresh pregame DK/FD quotes; existing snapshot retained")
        return 1
    output = {
        "source": "sportsgameodds-v2", "status": "ok", "sport": sport,
        "markets_requested": sorted(requested), "fetched_at": now.isoformat(),
        "odds": rows,
    }
    path = Path("feed") / (sport + ".json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    if sport != "mma_mixed_martial_arts":
        Path("feed/latest.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print("SportsGameOdds: published", len(rows), "fresh DK/FD quotes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
