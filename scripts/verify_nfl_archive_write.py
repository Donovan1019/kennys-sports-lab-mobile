#!/usr/bin/env python3
"""Verify a scheduled NFL source refresh actually persisted its pregame archive."""
import argparse
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def parse(value):
    t = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("timezone missing")
    return t.astimezone(dt.timezone.utc)

def verify(kind, root=ROOT):
    field = "source_games_fetched_at" if kind == "inputs" else "fetched_at"
    name = "independent_game_inputs.json" if kind == "inputs" else "americanfootball_nfl.json"
    feed = json.loads((root / "feed" / name).read_text())
    source_stamp = parse(feed[field])
    now = dt.datetime.now(dt.timezone.utc)
    if not now - dt.timedelta(hours=8) <= source_stamp <= now + dt.timedelta(minutes=2):
        raise ValueError("source feed is stale or future-dated")
    archive = root / "archive/nfl_moneyline" / kind / (source_stamp.strftime("%Y%m%dT%H%M%SZ") + ".json")
    if not archive.is_file():
        raise FileNotFoundError("source refreshed but matching archive file absent: " + str(archive))
    payload = json.loads(archive.read_text())
    if parse(payload["source_timestamp"]) != source_stamp:
        raise ValueError("archive source timestamp mismatch")
    key = "games" if kind == "inputs" else "odds"
    if not isinstance(payload.get(key), list) or not payload[key]:
        raise ValueError("archive has no pregame records")
    print(json.dumps({"status": "PASS", "kind": kind, "archive_file": str(archive.relative_to(root)), "pregame_records": len(payload[key])}))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["inputs", "odds"])
    args = parser.parse_args()
    verify(args.kind)
