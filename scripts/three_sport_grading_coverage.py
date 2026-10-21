"""Explain why archived forecasts have not yet been graded, without weakening strict matching."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from scripts.forecast_ledger import timestamp

SPORTS = (("basketball_nba", "nba"), ("icehockey_nhl", "nhl"), ("americanfootball_nfl", "nfl"))

def audit(root=Path("feed"), now=None):
    now = now or datetime.now(timezone.utc)
    results = []
    for sport, code in SPORTS:
        ledger = json.loads((root / f"{sport}_forecast_ledger.json").read_text())
        completed = json.loads((root / f"{code}_completed_games.json").read_text())
        outcomes = json.loads((root / f"{sport}_forecast_outcomes.json").read_text())
        earliest = {}
        for f in ledger.get("forecasts", []):
            start, at = timestamp(f.get("event_start")), timestamp(f.get("forecast_at"))
            if not start or not at or at >= start or not f.get("event_id"):
                continue
            key = f["event_id"]
            if key not in earliest or at < timestamp(earliest[key]["forecast_at"]):
                earliest[key] = f
        scored_ids = {r.get("forecast_id") for r in outcomes.get("scored", [])}
        counts = {"scored": 0, "upcoming": 0, "awaiting_final_result": 0,
                  "completed_unmatched": 0}
        examples = []
        for f in earliest.values():
            start = timestamp(f["event_start"])
            if f.get("forecast_id") in scored_ids:
                status = "scored"
            elif start > now:
                status = "upcoming"
            else:
                matching = [g for g in completed.get("games", [])
                            if g.get("home") == f.get("home") and g.get("away") == f.get("away")
                            and timestamp(g.get("date"))
                            and abs((timestamp(g["date"]) - start).total_seconds()) <= 1200]
                status = "completed_unmatched" if matching else "awaiting_final_result"
            counts[status] += 1
            if status == "completed_unmatched" and len(examples) < 5:
                examples.append({"event_id": f["event_id"], "event_start": f["event_start"]})
        results.append({"sport": sport, "unique_events": len(earliest),
                        "counts": counts, "unmatched_examples": examples})
    return {"checked_at": now.isoformat(), "sports": results, "paid_api_calls": 0,
            "note": "Awaiting final result also includes missing or mismatched result identifiers; no unverified game is scored."}

def main():
    output = Path("feed/three_sport_grading_coverage.json")
    result = audit()
    output.write_text(json.dumps(result, indent=2) + "\n")
    for item in result["sports"]:
        print(item["sport"], item["counts"])

if __name__ == "__main__":
    main()
