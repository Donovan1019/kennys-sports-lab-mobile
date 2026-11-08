#!/usr/bin/env python3
"""Join immutable pregame NFL snapshots with existing completed games.

Never treat outcomes as features or infer predictions from final scores.
Only exact event IDs are eligible for an outcome match.
"""
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UTC = dt.timezone.utc

def parse(value):
    if not isinstance(value, str):
        raise ValueError("timestamp missing")
    value = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("timezone missing")
    return value.astimezone(UTC)

def join(root=ROOT):
    path = root / "feed" / "nfl_completed_games.json"
    results = json.loads(path.read_text())
    settled = {}
    for game in results.get("games", []):
        if not all(k in game for k in ("event_id", "date", "away", "home", "away_score", "home_score")):
            continue
        key = str(game["event_id"])
        if key in settled:
            raise ValueError("duplicate completed event ID: " + key)
        settled[key] = game
    rows = []
    for file in sorted((root / "archive" / "nfl_moneyline" / "inputs").glob("*.json")):
        snapshot = json.loads(file.read_text())
        snap_time = parse(snapshot["source_timestamp"])
        for game in snapshot.get("games", []):
            kickoff = parse(game["commence_time"])
            if not snap_time < kickoff:
                raise ValueError("non-pregame input snapshot")
            for team in game.get("teams", []):
                for score in team.get("score_history", []):
                    if parse(score["date"]) >= snap_time:
                        raise ValueError("future scoring history in snapshot")
            event_id = str(game.get("event_id", ""))
            result = settled.get(event_id)
            if not result:
                continue
            if (game.get("away"), game.get("home")) != (result["away"], result["home"]):
                raise ValueError("team mismatch for event " + event_id)
            if abs((parse(result["date"]) - kickoff).total_seconds()) > 60 * 60 * 12:
                raise ValueError("kickoff mismatch for event " + event_id)
            away_score = int(result["away_score"])
            home_score = int(result["home_score"])
            if min(away_score, home_score) < 0:
                raise ValueError("negative final score")
            rows.append({
                "event_id": event_id,
                "snapshot_timestamp": snap_time.isoformat(),
                "kickoff": kickoff.isoformat(),
                "away": game["away"],
                "home": game["home"],
                "winner": "away" if away_score > home_score else "home" if home_score > away_score else "tie",
                "away_score": away_score,
                "home_score": home_score,
                "source_file": str(file.relative_to(root)),
                "evaluation_only": True,
            })
    return {"joined_snapshots": len(rows), "unique_games": len({r["event_id"] for r in rows}), "rows": rows,
            "note": "Outcomes for evaluation only; no predictions, calibrated probabilities or betting recommendations generated."}

if __name__ == "__main__":
    print(json.dumps(join(), indent=2))
