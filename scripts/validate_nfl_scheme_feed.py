#!/usr/bin/env python3
"""Validate licensed/authorized NFL scheme charting before publishing.

Input JSON: {"source": str, "generated_at": ISO8601, "rows": [
 {"event_id": str, "team": str, "side": "home"|"away",
  "coverage": "man"|"zone"|"cover0"..."cover6"|"blitz"|"pressure",
  "snaps": nonnegative int, "opportunities": positive int,
  "source_url": https URL, "verified": true}
]}
Never manufacture coverage labels from aggregate boxscores.
"""
import argparse
import datetime as dt
import json
import pathlib
import urllib.parse

ALLOWED = {"man", "zone", "cover0", "cover1", "cover2", "cover3", "cover4", "cover6", "blitz", "pressure"}

def validate(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("rows"), list):
        raise ValueError("rows must be a list")
    if not isinstance(payload.get("source"), str) or not payload["source"].strip():
        raise ValueError("source required")
    stamp = dt.datetime.fromisoformat(payload["generated_at"].replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("generated_at must include timezone")
    if payload.get("source") == "not-connected" and payload["rows"]:
        raise ValueError("unconnected source cannot publish verified rows")
    seen = set()
    for row in payload["rows"]:
        if not isinstance(row, dict):
            raise ValueError("row must be object")
        for key in ("event_id", "team", "coverage"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(key + " required")
        if row["coverage"] not in ALLOWED or row.get("side") not in ("home", "away"):
            raise ValueError("invalid coverage or side")
        if row.get("verified") is not True:
            raise ValueError("unverified scheme row")
        url = urllib.parse.urlparse(row.get("source_url", ""))
        if url.scheme != "https" or not url.netloc:
            raise ValueError("https source_url required")
        for key in ("snaps", "opportunities"):
            if type(row.get(key)) is not int:
                raise ValueError(key + " must be integer")
        if row["opportunities"] <= 0 or not 0 <= row["snaps"] <= row["opportunities"]:
            raise ValueError("invalid snap denominator")
        if row.get("team") != row["team"].strip():
            raise ValueError("team must be normalized")
        identity = (row["event_id"], row["side"], row["coverage"])
        if identity in seen:
            raise ValueError("duplicate scheme row")
        seen.add(identity)
    return payload

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--output", default="feed/nfl_verified_scheme.json")
    args = parser.parse_args()
    payload = validate(json.loads(pathlib.Path(args.input).read_text()))
    pathlib.Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.output).write_text(json.dumps(payload, indent=2) + "\n")

if __name__ == "__main__":
    main()
