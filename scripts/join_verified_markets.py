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
        return (row["sport"], event, row["market"], selection.strip().casefold(), float(point))
    return (row["sport"], event, row["market"], selection.strip().casefold(), None)

def mapped_quote_key(model, quote):
    """Map home/away only when both team names and source event ordering agree.

    The provider's "Away @ Home" convention is required. Never infer from
    abbreviations, fuzzy matches, or model probabilities.
    """
    key = contract(quote)
    if key is None:
        return None
    side = model.get("selection_id")
    if not isinstance(side, str) or side.strip().casefold() not in ("home", "away"):
        return contract(model) if contract(model) == key else None
    home, away = model.get("home_team"), model.get("away_team")
    event = model.get("event")
    if not all(isinstance(v, str) and v.strip() for v in (home, away, event)):
        return None
    participants = event.split(" @ ")
    if len(participants) != 2 or [v.strip().casefold() for v in participants] != [away.strip().casefold(), home.strip().casefold()]:
        return None
    expected = home if side.strip().casefold() == "home" else away
    if quote.get("selection_id", "").strip().casefold() != expected.strip().casefold():
        return None
    return (model["sport"], model["event_id"], model["market"], side.strip().casefold(), key[-1])

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
        if not isinstance(q, dict):
            continue
        key = contract(q)
        if key is None:
            continue
        m = models_by_key.get(key)
        if m is None:
            # Only permit explicit, source-verified home/away team mapping.
            m = next((candidate for mk, candidate in models_by_key.items()
                      if mk[0] == key[0] and mk[1] == key[1] and mk[2] == key[2]
                      and mk[4] == key[4] and mapped_quote_key(candidate, q) == mk), None)
        if not m or q.get("price_verified") is not True:
            continue
        # Provider event IDs alone are insufficient when event participant labels
        # conflict. Reject a quote that explicitly names a different matchup.
        quote_event = q.get("event")
        if quote_event is not None and (
            not isinstance(quote_event, str) or
            quote_event.strip().casefold() != str(m.get("event", "")).strip().casefold()
        ):
            continue
        if not timestamp(m.get("start_time")) or timestamp(m.get("start_time")) != timestamp(q.get("start_time")):
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
    result["status"] = "VERIFIED" if result["edges"] else ("UNAVAILABLE" if not models_by_key or not rows(quotes, "quotes") else "NO_QUALIFIED_EDGES")
    if result["status"] == "UNAVAILABLE":
        result["reason"] = "No eligible independently verified model markets" if not models_by_key else "No fresh verified sportsbook quotes"
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
