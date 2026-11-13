#!/usr/bin/env python3
"""Fail closed on invalid NFL defensive matchup feed structure and samples."""
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSITIONS = ("overall", "qb", "rb", "wr", "te")
WINDOWS = ("season", "last4", "previous")
SIDES = ("home", "away")
SIGNED = {"rushing_yards_allowed", "receiving_yards_allowed"}

def validate(data):
    stamp = datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00"))
    if stamp.tzinfo is None or stamp > datetime.now(timezone.utc):
        raise ValueError("Invalid feed timestamp")
    if not isinstance(data.get("events"), list) or not data["events"]:
        raise ValueError("No matchup events")
    seen = set()
    examined = 0
    for event in data["events"]:
        eid = event["event_id"]
        if not eid or eid in seen:
            raise ValueError("Missing/duplicate event ID")
        seen.add(eid)
        for window in WINDOWS:
            for position in POSITIONS:
                for side in SIDES:
                    d = event["matchup_stats"][window][position][side]
                    if not isinstance(d, dict):
                        raise ValueError("Invalid matchup bucket")
                    for field, metric in d.items():
                        if field == "summary":
                            continue
                        value = metric["value"]
                        sample = metric["sample_size"]
                        eligible = metric["games_in_window"]
                        pct = metric["coverage_pct"]
                        if not isinstance(value, (int, float)) or not math.isfinite(value):
                            raise ValueError("Nonfinite metric")
                        if value < 0 and field not in SIGNED:
                            raise ValueError("Negative unsigned metric")
                        if any(type(x) is not int for x in (sample, eligible)):
                            raise ValueError("Noninteger sample count")
                        if not (1 <= sample <= eligible):
                            raise ValueError("Invalid sample coverage")
                        if window == "last4" and eligible > 4:
                            raise ValueError("Last-four exceeds four games")
                        if not isinstance(pct, (int, float)) or abs(pct - round(100 * sample / eligible, 1)) > 0.11:
                            raise ValueError("Inconsistent coverage percentage")
                        examined += 1
    if not examined:
        raise ValueError("No valid matchup metrics")
    return examined

if __name__ == "__main__":
    count = validate(json.loads((ROOT / "feed/americanfootball_nfl_defensive_comparison.json").read_text()))
    print("PASS: validated", count, "defensive metrics")
