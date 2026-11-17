#!/usr/bin/env python3
"""Read-only public Kalshi market snapshot for GitHub Pages."""
import json
import re
import sys
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://external-api.kalshi.com/trade-api/v2/markets"
SERIES = {"nba": ["KXNBAGAME"], "nfl": ["KXNFLGAME"], "nhl": ["KXNHLGAME"], "ncaab": ["KXNCAAMBGAME", "KXNCAABGAME"]}
FIELDS = ("ticker", "event_ticker", "title", "subtitle", "status", "close_time", "yes_bid_dollars", "yes_ask_dollars", "no_ask_dollars", "yes_bid", "yes_ask", "no_ask", "volume_fp")

def fetch(ticker):
    rows, cursor = [], None
    for _ in range(3):
        params = {"series_ticker": ticker, "status": "open", "limit": 200}
        if cursor:
            params["cursor"] = cursor
        request = Request(BASE + "?" + urlencode(params), headers={"Accept": "application/json", "User-Agent": "KennysSportsLab-ReadOnly/1.0"})
        for attempt in range(3):
            try:
                with urlopen(request, timeout=18) as response:
                    payload = json.load(response)
                break
            except (HTTPError, URLError, TimeoutError) as error:
                if attempt == 2:
                    raise RuntimeError(f"{ticker}: {type(error).__name__}: {error}") from error
                time.sleep(2 ** attempt)
        rows.extend(payload.get("markets") or [])
        cursor = payload.get("cursor")
        if not cursor:
            break
    return rows

MONTHS = {name: index for index, name in enumerate(("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"), 1)}
GAME_DATE = re.compile(r"-(\d{2})(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)(\d{1,2})(?:[A-Z]|$)")

def game_date_from_ticker(market):
    """Conservative day-level extraction; not a confirmed tipoff time."""
    ticker = market.get("event_ticker") or market.get("ticker") or ""
    match = GAME_DATE.search(ticker)
    if not match:
        return None
    try:
        return datetime(2000 + int(match.group(1)), MONTHS[match.group(2)], int(match.group(3))).date()
    except ValueError:
        return None

def main():
    markets, failures = {}, []
    for sport, tickers in SERIES.items():
        for ticker in tickers:
            try:
                rows = fetch(ticker)
                print(f"{ticker}: {len(rows)} markets")
                for market in rows:
                    if market.get("ticker") and market.get("status") in ("open", "active"):
                        markets[market["ticker"]] = {**{key: market[key] for key in FIELDS if key in market}, "sport": sport}
            except Exception as error:
                failures.append(str(error))
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        raise SystemExit("Feed incomplete: preserving previous snapshot.")
    now = datetime.now(timezone.utc)
    upcoming = []
    today_et = now.astimezone(ZoneInfo('America/New_York')).date()
    excluded_past_games = 0
    for market in markets.values():
        game_day = game_date_from_ticker(market)
        if game_day is not None and game_day < today_et:
            excluded_past_games += 1
            continue
        if game_day is not None:
            market['game_date_et'] = game_day.isoformat()
        try:
            close = datetime.fromisoformat(market["close_time"].replace("Z", "+00:00"))
        except (KeyError, ValueError, AttributeError):
            continue
        if close > now:
            upcoming.append(market)
    upcoming.sort(key=lambda m: (m["close_time"], m["ticker"]))
    per_sport = {sport: 0 for sport in SERIES}
    selected = []
    for market in upcoming:
        sport = market["sport"]
        if per_sport[sport] < 500:
            selected.append(market)
            per_sport[sport] += 1
    snapshot = {"source": "Kalshi public REST API", "fetched_at": now.isoformat(), "series_checked": sum(map(len, SERIES.values())), "market_counts": per_sport, "excluded_past_game_dates": excluded_past_games, "markets": selected}
    target = Path("data/kalshi-markets.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Saved {len(snapshot['markets'])} markets")

if __name__ == "__main__":
    main()
