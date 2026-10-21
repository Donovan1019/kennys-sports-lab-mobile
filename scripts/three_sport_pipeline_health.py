"""Free-first three-sport pipeline health audit. No external calls."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

SPORTS = ("basketball_nba", "icehockey_nhl", "americanfootball_nfl")

def audit(root=Path("feed"), now=None):
    now = now or datetime.now(timezone.utc)
    reports = []
    for sport in SPORTS:
        files = {}
        errors = []
        for suffix in ("forecast_ledger", "forecast_outcomes", "market_consensus", "market_baseline_ledger"):
            path = root / f"{sport}_{suffix}.json"
            if not path.exists():
                errors.append(f"missing_{suffix}")
                continue
            try:
                data = json.loads(path.read_text())
                if not isinstance(data, dict):
                    raise ValueError("expected object")
                files[suffix] = data
            except (ValueError, OSError):
                errors.append(f"invalid_{suffix}")
        ledger = files.get("forecast_ledger", {})
        forecasts = ledger.get("forecasts", [])
        if not isinstance(forecasts, list):
            errors.append("invalid_forecast_list")
            forecasts = []
        if not forecasts:
            errors.append("no_archived_forecasts")
        # Detect a stopped forecast pipeline using explicit forecast creation times.
        # Missing/unparseable timestamps remain unknown rather than falsely stale.
        timestamps = []
        for row in forecasts:
            if not isinstance(row, dict):
                continue
            raw = row.get("forecast_at") or row.get("created_at") or row.get("asof")
            if not isinstance(raw, str):
                continue
            try:
                stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if stamp.tzinfo is not None:
                    timestamps.append(stamp.astimezone(timezone.utc))
            except ValueError:
                pass
        newest = max(timestamps) if timestamps else None
        # NBA/NHL can be off-season, and NFL has weekly gaps. Mark as warning
        # only when recent market events demonstrate an active upcoming slate.
        market_events = files.get("market_consensus", {}).get("events", [])
        if not isinstance(market_events, list):
            errors.append("invalid_market_events")
            market_events = []
        if newest and market_events and now - newest > timedelta(days=8):
            errors.append("stale_forecasts_over_8_days_with_market_events")
        outcomes = files.get("forecast_outcomes", {}).get("scored", [])
        if not isinstance(outcomes, list):
            errors.append("invalid_scored_list")
            outcomes = []
        reports.append({"sport": sport, "status": "attention_required" if errors else "operational",
                        "forecast_count": len(forecasts), "scored_count": len(outcomes),
                        "newest_forecast_at": newest.isoformat() if newest else None,
                        "issues": errors,
                        "note": "Zero scored forecasts alone is not an error; future games may be pending."})
    return {"checked_at": now.isoformat(), "status": "attention_required" if any(r["issues"] for r in reports) else "operational",
            "sports": reports, "paid_api_calls": 0}

def main():
    report = audit()
    output = Path("feed/three_sport_pipeline_health.json")
    output.write_text(json.dumps(report, indent=2) + "\n")
    for sport in report["sports"]:
        print(f"{sport['sport']}: {sport['status']} issues={','.join(sport['issues']) or 'none'}")
    if report["status"] != "operational":
        print("::warning::One or more sports have missing or malformed pipeline inputs; see feed/three_sport_pipeline_health.json")

if __name__ == "__main__":
    main()
