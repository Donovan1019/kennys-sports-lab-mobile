#!/usr/bin/env python3
"""Join independently simulated model markets to verified sportsbook quotes.

Never estimates model probabilities or marks quotes verified. Strict exact contract.
Input files are independently published JSON lists or objects with 'markets'/'quotes'.
"""
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from scripts.build_market_edges import build, timestamp

SPORTS = {"NBA", "NHL", "NFL", "NCAAB"}
MARKETS = {"ML", "SPREAD", "TOTAL"}

def rows(obj, key):
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict) and isinstance(obj.get(key), list):
        return obj[key]
    return []

def contract(row):
    if not isinstance(row, dict):
        return None
    if row.get("sport") not in SPORTS or row.get("market") not in MARKETS:
        return None
    event = row.get("event_id")
    selection = row.get("selection_id")
    if not isinstance(event, str) or not event.strip() or not isinstance(selection, str) or not selection.strip():
        return None
    point = row.get("point")
    if row["market"] in ("SPREAD", "TOTAL"):
        if type(point) not in (int, float) or not math.isfinite(point):
            return None
        return (row["sport"], event, row["market"], selection, float(point))
    return (row["sport"], event, row["market"], selection, None)

def join(models, quotes, now=None):
    now = now or datetime.now(timezone.utc)
    models_by_key = {}
    for m in rows(models, "markets"):
        key = contract(m)
        if key is None or m.get("simulation_status") != "COMPLETE" or m.get("data_status") != "VERIFIED":
            continue
        if m.get("lineup_status") not in ("CONFIRMED", "VERIFIED"):
            continue
        stamp = timestamp(m.get("model_generated_at"))
        if not stamp or not 0 <= (now-stamp).total_seconds() <= 3600:
            continue
        previous = models_by_key.get(key)
        if previous is None or stamp > timestamp(previous["model_generated_at"]):
            models_by_key[key] = m
    candidates = []
    for q in rows(quotes, "quotes"):
        key = contract(q)
        m = models_by_key.get(key)
        if not m or q.get("price_verified") is not True:
            continue
        if m.get("start_time") != q.get("start_time"):
            continue
        row = {**m, "odds": q.get("odds"), "source": q.get("source"),
               "odds_timestamp": q.get("odds_timestamp"), "price_verified": True,
               "event": m.get("event"), "selection": m.get("selection")}
        if key[-1] is not None:
            row["point"] = key[-1]
        candidates.append(row)
    result = build(candidates, now)
    result["matched_contracts"] = len(candidates)
    result["model_contracts"] = len(models_by_key)
    result["quote_contracts"] = len(rows(quotes, "quotes"))
    result["status"] = "VERIFIED" if result["edges"] else "NO_QUALIFIED_EDGES"
    return result

def main():
    model_path = Path("data/verified_model_markets.json")
    quote_path = Path("data/verified_sportsbook_quotes.json")
    output = Path("data/market_edges.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    if not model_path.exists() or not quote_path.exists():
        missing = [str(p) for p in (model_path,quote_path) if not p.exists()]
        report = {"edges": [], "status": "UNAVAILABLE", "reason": "Missing independent verified market inputs: "+", ".join(missing)}
    else:
        try:
            report = join(json.loads(model_path.read_text()), json.loads(quote_path.read_text()))
        except (ValueError, OSError, TypeError) as exc:
            report = {"edges": [], "status": "UNAVAILABLE", "reason": "Invalid upstream verified input: "+type(exc).__name__}
    output.write_text(json.dumps(report, indent=2)+"\n")
    print(report["status"],len(report["edges"]))

if __name__ == "__main__":
    main()
