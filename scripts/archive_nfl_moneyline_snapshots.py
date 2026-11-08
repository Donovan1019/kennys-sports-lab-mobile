#!/usr/bin/env python3
"""Append-only, source-timestamped NFL research snapshots for future walk-forward validation.

Archives are NOT calibrated predictions. Never use outcomes occurring after snapshot time
as model inputs. Fail closed on malformed, future-dated or stale source timestamps.
"""
import argparse
import datetime as dt
import json
from pathlib import Path

UTC = dt.timezone.utc
ROOT = Path(__file__).resolve().parents[1]
MAX_AGE = dt.timedelta(hours=8)


def parse(value):
    if not isinstance(value, str):
        raise ValueError("missing timestamp")
    result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timezone missing")
    return result.astimezone(UTC)


def archive(kind):
    now = dt.datetime.now(UTC)
    source = ROOT / "feed" / ("independent_game_inputs.json" if kind == "inputs" else "americanfootball_nfl.json")
    payload = json.loads(source.read_text(encoding="utf-8"))
    field = "source_games_fetched_at" if kind == "inputs" else "fetched_at"
    source_time = parse(payload.get(field))
    if source_time > now + dt.timedelta(minutes=2) or now - source_time > MAX_AGE:
        print("SKIP: stale or future-dated", kind, "source", source_time.isoformat())
        return
    if kind == "inputs":
        games = payload.get("games")
        if not isinstance(games, list) or not games:
            raise ValueError("missing input games")
        for game in games:
            if parse(game["commence_time"]) <= source_time:
                continue
            for team in game.get("teams", []):
                for item in team.get("score_history", []):
                    if parse(item["date"]) >= source_time:
                        raise ValueError("post-snapshot scoring history detected")
        content = {"source_timestamp": source_time.isoformat(), "source": payload.get("source"),
                   "games": [g for g in games if parse(g["commence_time"]) > source_time]}
    else:
        rows = payload.get("odds")
        if not isinstance(rows, list) or not rows:
            print("SKIP: no odds to archive")
            return
        content = {"source_timestamp": source_time.isoformat(), "source": payload.get("source"),
                   "odds": [r for r in rows if r.get("market") == "h2h"
                            and r.get("bookmaker") in ("draftkings", "fanduel")
                            and parse(r["commence_time"]) > source_time
                            and parse(r["updated_at"]) <= source_time + dt.timedelta(minutes=2)]}
        if not content["odds"]:
            print("SKIP: no pregame moneyline odds")
            return
    stamp = source_time.strftime("%Y%m%dT%H%M%SZ")
    dest = ROOT / "archive" / "nfl_moneyline" / kind / (stamp + ".json")
    if dest.exists():
        print("Existing snapshot retained:", dest)
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(content, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")
    print("Archived", kind, "source snapshot", dest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("inputs", "odds"))
    archive(parser.parse_args().kind)
