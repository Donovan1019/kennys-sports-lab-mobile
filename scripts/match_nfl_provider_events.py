#!/usr/bin/env python3
"""Conservative ESPN-to-sportsbook NFL event crosswalk.

Never join unrelated provider IDs directly. Require exact normalized team names
and kickoff proximity, and reject ambiguous or reused matches.
"""
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def parse(value):
    t = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return t.astimezone(dt.timezone.utc)

def normalize(name):
    return " ".join(str(name).casefold().replace(".", "").split())

def match(inputs, odds, tolerance_minutes=15):
    grouped = {}
    for row in odds:
        if row.get("market") != "h2h" or row.get("bookmaker") not in ("draftkings", "fanduel"):
            continue
        key = (str(row.get("event_id", "")), str(row.get("commence_time", "")))
        grouped.setdefault(key, []).append(row)
    matches, warnings = [], []
    used = set()
    for game in inputs:
        teams = (normalize(game["away"]), normalize(game["home"]))
        kickoff = parse(game["commence_time"])
        candidates = []
        for key, rows in grouped.items():
            if abs((parse(key[1]) - kickoff).total_seconds()) > tolerance_minutes * 60:
                continue
            selections = {normalize(r.get("selection")) for r in rows}
            if not set(teams).issubset(selections):
                continue
            candidates.append((key, rows))
        if len(candidates) != 1:
            warnings.append({"espn_event_id": str(game.get("event_id")), "reason": "ambiguous" if candidates else "unmatched"})
            continue
        key, rows = candidates[0]
        if key in used:
            warnings.append({"espn_event_id": str(game.get("event_id")), "reason": "sportsbook event reused"})
            continue
        used.add(key)
        matches.append({"espn_event_id": str(game["event_id"]), "odds_event_id": key[0],
                        "kickoff": game["commence_time"], "quote_count": len(rows),
                        "bookmakers": sorted({r["bookmaker"] for r in rows})})
    return {"matched_games": len(matches), "matches": matches, "warnings": warnings,
            "note": "Identity-only matching; quote freshness and odds pricing must be validated separately."}

if __name__ == "__main__":
    root = ROOT / "feed"
    a = json.loads((root / "independent_game_inputs.json").read_text())
    b = json.loads((root / "americanfootball_nfl.json").read_text())
    print(json.dumps(match(a["games"], b["odds"]), indent=2))
