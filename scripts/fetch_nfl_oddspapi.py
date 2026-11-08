#!/usr/bin/env python3
"""Fail-closed NFL OddsPapi moneyline fallback. Never infer a team from outcome ID."""
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from scripts.fetch_odds import validate_rows

BASE = "https://api.oddspapi.io/v4/"
UTC = dt.timezone.utc

def request(path, key, params=None):
    query = dict(params or {}, apiKey=key)
    url = BASE + path + "?" + urllib.parse.urlencode(query)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "KennysSportsLab/1.0"}), timeout=45) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError("OddsPapi " + path + " HTTP " + str(exc.code)) from None

def parse(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)

def normalize(fixture, response, now):
    kickoff = fixture.get("startTime")
    if not kickoff or parse(kickoff) <= now:
        return []
    home, away = fixture.get("participant1Name"), fixture.get("participant2Name")
    if not home or not away:
        return []
    rows = []
    boards = response.get("bookmakerOdds") or {}
    for book in ("draftkings", "fanduel"):
        board = boards.get(book) or {}
        if not board.get("bookmakerIsActive", False):
            continue
        for market_id in ("141", "143", "1422959"):
            market = (board.get("markets") or {}).get(market_id) or {}
            if not market.get("marketActive", False):
                continue
            found = {}
            for outcome in (market.get("outcomes") or {}).values():
                for player in (outcome.get("players") or {}).values():
                    if not player.get("active"):
                        continue
                    side = str(player.get("bookmakerOutcomeId") or "").strip().lower()
                    # Do not assume participant order or map opaque numeric IDs.
                    if side not in ("home", "away"):
                        continue
                    updated = player.get("bookmakerChangedAt") or player.get("changedAt")
                    price = player.get("priceAmerican")
                    try:
                        number = int(price)
                        if not updated or number == 0:
                            continue
                        if parse(updated) > now + dt.timedelta(minutes=2) or now - parse(updated) > dt.timedelta(hours=8):
                            continue
                    except (ValueError, TypeError):
                        continue
                    found[side] = {"event": away + " @ " + home, "event_id": fixture.get("fixtureId"),
                                   "commence_time": kickoff, "sport": "americanfootball_nfl",
                                   "market": "h2h", "description": None, "player": None,
                                   "selection": home if side == "home" else away, "point": None,
                                   "price": number, "bookmaker": book, "updated_at": updated}
            if set(found) == {"home", "away"}:
                rows.extend([found["home"], found["away"]])
                break
    return rows

def main():
    key = os.getenv("ODDSPAPI_API_KEY")
    if not key:
        print("OddsPapi fallback unavailable: ODDSPAPI_API_KEY secret missing")
        return 2
    now = dt.datetime.now(UTC)
    try:
        account = request("account", key)
        if not isinstance(account, dict) or account.get("error"):
            raise ValueError("account verification failed")
        print("OddsPapi account authentication succeeded")
        fixtures = request("fixtures", key, {"tournamentId": 31, "from": now.date().isoformat(),
                                            "to": (now + dt.timedelta(days=7)).date().isoformat()})
        if not isinstance(fixtures, list):
            raise ValueError("unexpected fixtures response")
        rows = []
        for fixture in sorted(fixtures, key=lambda f: f.get("startTime") or ""):
            if fixture.get("hasOdds") and fixture.get("tournamentId") == 31 and fixture.get("startTime") and parse(fixture["startTime"]) > now:
                data = request("odds", key, {"fixtureId": fixture["fixtureId"], "bookmakers": "draftkings,fanduel"})
                if isinstance(data, dict):
                    rows.extend(normalize(fixture, data, now))
                if len(rows) >= 2:
                    break
        if not validate_rows(rows, "americanfootball_nfl", now):
            raise ValueError("no verified fresh NFL DK/FD moneyline with explicit home/away selection; existing feed retained")
        output = {"source": "oddspapi-v4", "status": "ok", "sport": "americanfootball_nfl",
                  "markets_requested": ["h2h"], "fetched_at": dt.datetime.now(UTC).isoformat(),
                  "remaining_credits": None, "odds": rows}
        for path in (Path("feed/americanfootball_nfl.json"), Path("feed/latest.json")):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(output, indent=2) + "\n")
        print("Published", len(rows), "verified OddsPapi NFL moneyline selections")
        return 0
    except (RuntimeError, ValueError, KeyError, urllib.error.URLError) as exc:
        print("OddsPapi fallback failed safely:", str(exc))
        return 1

if __name__ == "__main__":
    sys.exit(main())
