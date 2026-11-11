#!/usr/bin/env python3
"""Audit existing sport pipelines before publishing actionable betting candidates."""
import json
from datetime import datetime, timezone
from pathlib import Path

SOURCES = {
 "NBA": ("feed/basketball_nba_pregame_research.json", "feed/basketball_nba_market_consensus.json"),
 "NHL": ("feed/icehockey_nhl_pregame_research.json", "feed/icehockey_nhl_market_consensus.json"),
 "NFL": ("feed/americanfootball_nfl_pregame_research.json", "feed/americanfootball_nfl_market_consensus.json"),
 "NCAAB": ("feed/basketball_ncaab_pregame_research.json", "feed/basketball_ncaab_market_consensus.json"),
}
def inspect(root=Path(".")):
    sports = {}
    for sport, paths in SOURCES.items():
        result = {}
        for label, path in zip(("model", "market"), paths):
            file = root / path
            if not file.is_file():
                result[label] = {"status": "MISSING", "path": path, "events": 0}
                continue
            try:
                obj = json.loads(file.read_text())
                events = obj.get("events", []) if isinstance(obj, dict) else []
                count = len(events) if isinstance(events, list) else 0
                status = obj.get("status", "UNVERIFIED") if isinstance(obj, dict) else "INVALID"
                result[label] = {"status": status, "path": path, "events": count}
            except (OSError, ValueError, TypeError):
                result[label] = {"status": "INVALID", "path": path, "events": 0}
        result["betting_ready"] = False
        result["reason"] = ("No standardized verified model-and-odds candidate feed; research-only files "
                            "must not be promoted into betting recommendations")
        sports[sport] = result
    candidates = root / "data/model_market_candidates.json"
    candidate_count = 0
    if candidates.is_file():
        try:
            raw = json.loads(candidates.read_text())
            rows = raw if isinstance(raw, list) else raw.get("edges", [])
            candidate_count = len(rows) if isinstance(rows, list) else 0
        except (ValueError, OSError, TypeError, AttributeError):
            pass
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "status": "CANDIDATES_PRESENT" if candidate_count else "UNAVAILABLE", "candidate_count": candidate_count, "sports": sports}

if __name__ == "__main__":
    output = Path("data/market_edge_readiness.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inspect(), indent=2) + "\n")
    print(output.read_text())
