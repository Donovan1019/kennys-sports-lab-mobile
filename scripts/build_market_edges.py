#!/usr/bin/env python3
"""Normalize verified sport-model exports into homepage market edges.
Never estimates probabilities, simulates games, or fetches sportsbook prices.
Usage: python3 scripts/build_market_edges.py INPUT.json OUTPUT.json
INPUT is an array of model-produced verified market records, or {edges:[...]}.
"""
import json, math, pathlib, sys
from datetime import datetime, timezone

SPORTS = {"NBA", "NHL", "NFL", "NCAAB"}
MARKETS = {"ML", "SPREAD", "TOTAL"}

def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except (ValueError, TypeError, AttributeError):
        return None

def american_payout(odds):
    return odds / 100 if odds > 0 else 100 / -odds

def qualify(row, now):
    if not isinstance(row, dict) or row.get("sport") not in SPORTS or row.get("market") not in MARKETS:
        return None
    if not all(isinstance(row.get(k), str) and row[k].strip() for k in ("event", "selection", "source")):
        return None
    if type(row.get("odds")) not in (int, float) or not math.isfinite(row["odds"]) or abs(row["odds"]) < 100:
        return None
    # Market contracts must identify the exact event, selection and point.
    # Spread/total prices without an explicit line cannot be compared safely.
    if row["market"] in ("SPREAD", "TOTAL"):
        point = row.get("point")
        if type(point) not in (int, float) or not math.isfinite(point):
            return None
    # Explicit model provenance prevents a bookmaker price being relabeled as a model forecast.
    if row.get("model_source") in (None, "", "sportsbook", "implied_odds"):
        return None
    if row.get("model_generated_at") is None or timestamp(row.get("model_generated_at")) is None:
        return None
    if not 0 <= (now - timestamp(row["model_generated_at"])).total_seconds() <= 3600:
        return None
    p = row.get("model_probability")
    if type(p) not in (int, float) or not math.isfinite(p) or not 0 < p < 1:
        return None
    if type(row.get("simulations")) is not int or row["simulations"] < 1000:
        return None
    if row.get("lineup_status") not in ("CONFIRMED", "VERIFIED"):
        return None
    if row.get("simulation_status") != "COMPLETE" or row.get("price_verified") is not True or row.get("data_status") != "VERIFIED" or row.get("lineup_status") == "UNVERIFIED":
        return None
    odds_at, start = timestamp(row.get("odds_timestamp")), timestamp(row.get("start_time"))
    if not odds_at or not start or not 0 <= (now - odds_at).total_seconds() <= 900 or start <= now:
        return None
    ev = p * american_payout(row["odds"]) - (1 - p)
    if ev <= 0:
        return None
    return row | {"ev": round(ev, 8)}

def build(records, now=None):
    now = now or datetime.now(timezone.utc)
    qualified = [v for row in records if (v := qualify(row, now))]
    # Do not repeat an identical selection/price across provider duplicates.
    unique = {}
    for row in qualified:
        key = (row["sport"], row["event"], row["market"], row["selection"], row.get("point"), row["source"])
        if key not in unique or row["odds_timestamp"] > unique[key]["odds_timestamp"]:
            unique[key] = row
    return {"generated_at": now.isoformat(), "edges": sorted(unique.values(), key=lambda r: -r["ev"])}

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: build_market_edges.py INPUT.json OUTPUT.json")
    source = json.loads(pathlib.Path(sys.argv[1]).read_text())
    rows = source if isinstance(source, list) else source["edges"]
    if not isinstance(rows, list):
        raise SystemExit("Expected list of market records")
    output = pathlib.Path(sys.argv[2])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build(rows), indent=2) + "\n")
