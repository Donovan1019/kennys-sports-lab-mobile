#!/usr/bin/env python3
"""Merge two valid append-only pregame forecast ledgers without losing records."""
import json
import sys
from pathlib import Path

def load(path):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("forecasts"), list):
        raise ValueError(f"Invalid NFL forecast ledger: {path}")
    return value["forecasts"]

def merge(existing, incoming):
    result = {}
    for row in existing + incoming:
        if not isinstance(row, dict) or not isinstance(row.get("forecast_id"), str) or not row["forecast_id"]:
            raise ValueError("Invalid forecast record identity")
        key = row["forecast_id"]
        if key in result and result[key] != row:
            raise ValueError(f"Conflicting forecast identity: {key}")
        result[key] = row
    return {"status": "RESEARCH_ONLY", "forecasts": list(result.values())}

def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: merge_nfl_prop_forecast_ledgers.py destination incoming")
    dest, incoming = sys.argv[1:]
    combined = merge(load(dest), load(incoming))
    Path(dest).write_text(json.dumps(combined, indent=2) + "\n", encoding="utf-8")
    print(f"Preserved {len(combined['forecasts'])} unique pregame forecasts")

if __name__ == "__main__":
    main()
