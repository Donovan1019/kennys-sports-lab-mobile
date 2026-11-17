#!/usr/bin/env python3
"""Read-only public Kalshi market snapshot for GitHub Pages."""
import json
import sys
import time
from datetime import datetime, timezone
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
    snapshot = {"source": "Kalshi public REST API", "fetched_at": datetime.now(timezone.utc).isoformat(), "series_checked": sum(map(len, SERIES.values())), "markets": sorted(markets.values(), key=lambda m: (m.get("close_time") or "", m["ticker"]))[:500]}
    target = Path("data/kalshi-markets.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Saved {len(snapshot['markets'])} markets")

if __name__ == "__main__":
    main()
