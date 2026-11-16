#!/usr/bin/env python3
"""Research-only NFL ML estimates from ESPN pregame scoring histories, never odds."""
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_SOURCE_AGE_SECONDS = 48 * 3600

def parse(value):
    d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if d.tzinfo is None:
        raise ValueError("Timezone required")
    return d.astimezone(timezone.utc)

def build(odds, inputs, now):
    if odds.get("sport") != "americanfootball_nfl" or odds.get("status") != "ok":
        raise ValueError("Invalid NFL odds")
    source_time = parse(inputs["source_games_fetched_at"])
    if not 0 <= (now - source_time).total_seconds() <= MAX_SOURCE_AGE_SECONDS:
        raise ValueError("NFL scoring history stale")
    odds_time = parse(odds["fetched_at"])
    if not 0 <= (now - odds_time).total_seconds() <= 24 * 3600:
        raise ValueError("NFL sportsbook snapshot stale")
    history = {}
    for game in inputs.get("games", []):
        for team in game.get("teams", []):
            name = team.get("team")
            if not name:
                continue
            valid = []
            for row in team.get("score_history", []):
                try:
                    date = parse(row["date"])
                    scored, allowed = float(row["scored"]), float(row["allowed"])
                except (KeyError, TypeError, ValueError, AttributeError):
                    continue
                if date >= source_time or date >= now or row.get("season_type") != 2:
                    continue
                if not all(math.isfinite(v) and 0 <= v <= 100 for v in (scored, allowed)):
                    continue
                valid.append((date, scored - allowed))
            valid.sort(reverse=True)
            if len(valid) >= 4:
                history[name] = valid[:8]
    predictions, seen = [], set()
    for row in odds.get("odds", []):
        eid, event = row.get("event_id"), row.get("event", "")
        if row.get("market") != "h2h" or not eid or eid in seen or " @ " not in event:
            continue
        seen.add(eid)
        try:
            kickoff = parse(row["commence_time"])
        except (KeyError, ValueError, TypeError, AttributeError):
            continue
        if kickoff <= now:
            continue
        away, home = event.split(" @ ", 1)
        if away not in history or home not in history:
            continue
        # Shrink historical margin towards league average, plus modest home advantage.
        def strength(name):
            games = history[name]
            return sum(margin for _, margin in games) / (len(games) + 4)
        margin = strength(home) - strength(away) + 1.5
        p_home = 1 / (1 + math.exp(-max(-30, min(30, margin / 10))))
        for team, probability in ((home, p_home), (away, 1 - p_home)):
            predictions.append({"event_id": str(eid), "team": team,
                                "win_probability": round(probability, 6),
                                "sample_games": len(history[team])})
    return {"status": "research_only", "sport": "americanfootball_nfl",
            "generated_at": now.isoformat(), "model_version": "nfl-score-margin-shrink-v1",
            "calibration_passed": False, "lineups_verified": False,
            "predictions": predictions}

def main():
    now = datetime.now(timezone.utc)
    try:
        odds = json.loads((ROOT / "feed/americanfootball_nfl.json").read_text())
        inputs = json.loads((ROOT / "feed/independent_game_inputs.json").read_text())
        result = build(odds, inputs, now)
        if not result["predictions"]:
            result["status"] = "unavailable"
            result["reason"] = "No upcoming NFL matchups with sufficient verified pregame history"
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as exc:
        result = {"status": "unavailable", "sport": "americanfootball_nfl",
                  "generated_at": now.isoformat(), "calibration_passed": False,
                  "predictions": [], "reason": str(exc)[:160]}
    (ROOT / "feed/nfl_ml_predictions.json").write_text(json.dumps(result, indent=2) + "\n")
    print("NFL independent ML research:", result["status"], len(result["predictions"]))

if __name__ == "__main__":
    main()
