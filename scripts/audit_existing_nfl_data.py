#!/usr/bin/env python3
"""Audit existing NFL datasets without fetching or inventing new records."""
import datetime as dt
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UTC = dt.timezone.utc

def parse(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)

def audit(root=ROOT, now=None):
    now = now or dt.datetime.now(UTC)
    feeds = root / "feed"
    result = {"checked_at": now.isoformat(), "sources": {}, "warnings": []}
    for key, filename, timestamp in (
        ("completed_games", "nfl_completed_games.json", "fetched_at"),
        ("schedule_inputs", "independent_game_inputs.json", "source_games_fetched_at"),
        ("sportsbook_odds", "americanfootball_nfl.json", "fetched_at"),
    ):
        path = feeds / filename
        if not path.exists():
            result["sources"][key] = {"status": "MISSING"}
            continue
        data = json.loads(path.read_text())
        fetched = parse(data[timestamp])
        age = (now - fetched).total_seconds() / 3600
        item = {"status": "FRESH" if 0 <= age <= 8 else "STALE", "timestamp": fetched.isoformat(), "age_hours": round(age, 2)}
        if key == "completed_games":
            games = data.get("games", [])
            valid = [g for g in games if all(k in g for k in ("event_id", "date", "away", "home", "away_score", "home_score"))]
            item.update({"games": len(games), "valid_final_scores": len(valid), "years": dict(Counter(parse(g["date"]).year for g in valid))})
            if len(valid) != len(games):
                result["warnings"].append("Completed games contain incomplete score records")
        elif key == "schedule_inputs":
            games = data.get("games", [])
            histories = [h for g in games for team in g.get("teams", []) for h in team.get("score_history", [])]
            item.update({"upcoming_games": len(games), "history_rows": len(histories), "season_classified_rows": sum(h.get("season_type") == 2 for h in histories)})
            if histories and any(h.get("season_type") != 2 for h in histories):
                result["warnings"].append("Schedule feed requires regular-season classified refresh")
        else:
            rows = data.get("odds", [])
            item.update({"quotes": len(rows), "nfl_moneylines": sum(r.get("market") == "h2h" and r.get("bookmaker") in ("draftkings", "fanduel") for r in rows)})
            if item["status"] != "FRESH":
                result["warnings"].append("Sportsbook feed is stale: never display as live prices")
        result["sources"][key] = item
    return result

if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
