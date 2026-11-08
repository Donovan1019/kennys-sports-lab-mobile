#!/usr/bin/env python3
"""Research-only NFL prop point-in-time line audit from existing graded snapshots."""
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "feed/nfl_prop_graded_snapshots.json"
OUTPUT = ROOT / "feed/nfl_prop_real_line_backtest.json"

def parse_time(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None

def implied(american):
    try:
        p = float(american)
        if abs(p) < 100:
            return None
        return 100 / (p + 100) if p > 0 else -p / (100 - p)
    except (TypeError, ValueError, ZeroDivisionError):
        return None

def audit(rows):
    groups = defaultdict(list)
    seen = set()
    exclusions = defaultdict(int)
    for row in rows:
        if not isinstance(row, dict):
            exclusions["invalid_record"] += 1
            continue
        quote, forecast, kickoff = [parse_time(row.get(k)) for k in ("quoted_at", "forecast_at", "kickoff")]
        if not all((quote, forecast, kickoff)) or not quote <= forecast < kickoff:
            exclusions["point_in_time_invalid"] += 1
            continue
        if row.get("outcome_verified") is not True:
            exclusions["unverified_outcome"] += 1
            continue
        try:
            line, outcome, prob = [float(row[k]) for k in ("line", "outcome", "model_probability")]
        except (KeyError, ValueError, TypeError):
            exclusions["missing_numeric_fields"] += 1
            continue
        if not 0 <= prob <= 1:
            exclusions["invalid_probability"] += 1
            continue
        over, under = implied(row.get("over_odds")), implied(row.get("under_odds"))
        if over is None or under is None:
            exclusions["missing_two_sided_odds"] += 1
            continue
        key = row.get("forecast_id") or (row.get("event_id"), row.get("player"), row.get("market"), line, row.get("bookmaker"))
        if key in seen:
            exclusions["duplicate"] += 1
            continue
        seen.add(key)
        if outcome == line:
            exclusions["push"] += 1
            continue
        groups[str(row.get("market") or "unknown")].append({
            "event_id": str(row.get("event_id") or ""),
            "date": kickoff.date().isoformat(),
            "prob": prob,
            "result": int(outcome > line),
            "over_implied": over,
            "under_implied": under,
        })
    markets = {}
    for market, values in sorted(groups.items()):
        n = len(values)
        events = len({v["event_id"] for v in values})
        dates = len({v["date"] for v in values})
        brier = sum((v["prob"] - v["result"]) ** 2 for v in values) / n
        baseline = sum((v["over_implied"] / (v["over_implied"] + v["under_implied"]) - v["result"]) ** 2 for v in values) / n
        markets[market] = {
            "samples": n, "distinct_events": events, "distinct_dates": dates,
            "model_brier": round(brier, 6), "no_vig_market_brier": round(baseline, 6),
            "model_minus_market_brier": round(brier - baseline, 6),
            "live_use_eligible": False,
            "status": "INSUFFICIENT_INDEPENDENT_EVENTS" if events < 20 else "RESEARCH_ONLY_REQUIRES_FUTURE_HOLDOUT",
        }
    return {
        "status": "RESEARCH_ONLY", "source": "feed/nfl_prop_graded_snapshots.json",
        "records_seen": len(rows), "exclusions": dict(exclusions),
        "markets": markets,
        "bet_eligibility": "BLOCKED",
        "limitations": "Snapshot observations from very few games, correlated players and multiple books; not an independent future holdout. No EV or SGP recommendation authorization.",
    }

def main():
    rows = json.loads(SOURCE.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("Expected list of graded snapshots")
    result = audit(rows)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
