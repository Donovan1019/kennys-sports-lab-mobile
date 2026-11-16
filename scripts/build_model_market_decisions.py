"""Cross-sport independent prediction and pricing decisions; never infer models from odds."""
import json
from datetime import datetime, timezone
from pathlib import Path
from scripts.model_market_pricing import evaluate

SPORTS = {
    "basketball_nba": ("nba_ml_predictions.json", "NBA"),
    "basketball_ncaab": ("ncaab_ml_predictions.json", "NCAAB"),
    "icehockey_nhl": ("nhl_ml_predictions.json", "NHL"),
}


def predictions_for(sport, model):
    result = {}
    if sport == "basketball_nba" and not (model.get("status") == "validated" and model.get("calibration_passed") is True):
        return result
    for row in model.get("predictions", []):
        eid = row.get("event_id")
        if not eid:
            continue
        if sport == "icehockey_nhl":
            if row.get("status") != "RESEARCH_ONLY" or " @ " not in (row.get("event") or ""):
                continue
            away, home = row["event"].split(" @ ", 1)
            for team, key in ((away, "away_win_probability"), (home, "home_win_probability")):
                result[(str(eid), team)] = row.get(key)
        else:
            result[(str(eid), row.get("team"))] = row.get("win_probability")
    return result


def build(snapshots, now=None):
    now = now or datetime.now(timezone.utc)
    decisions = []
    for sport, (odds, model) in snapshots.items():
        if odds.get("status") != "ok":
            continue
        model_stamp = model.get("generated_at")
        if model_stamp:
            try:
                model_time = datetime.fromisoformat(model_stamp.replace("Z", "+00:00"))
                age_seconds = (now - model_time).total_seconds()
                if model_time.tzinfo is None or age_seconds < 0 or age_seconds > 86400:
                    continue
            except (ValueError, TypeError, AttributeError):
                continue
        fetched_at = odds.get("fetched_at")
        if fetched_at:
            try:
                fetched_time = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
                age_seconds = (now - fetched_time).total_seconds()
                if fetched_time.tzinfo is None or age_seconds < 0 or age_seconds > 86400:
                    continue
            except (ValueError, TypeError, AttributeError):
                continue
        mapping = predictions_for(sport, model)
        for row in odds.get("odds", []):
            if row.get("market") != "h2h" or row.get("bookmaker") not in ("draftkings", "fanduel"):
                continue
            try:
                tip = datetime.fromisoformat(row["commence_time"].replace("Z", "+00:00"))
                if tip.tzinfo is None or tip <= now:
                    continue
            except (KeyError, ValueError, TypeError, AttributeError):
                continue
            p = mapping.get((str(row.get("event_id")), row.get("selection")))
            if p is None:
                continue
            # Research baselines remain visible as projections, but are never bet-certified.
            validated = sport == "basketball_nba" and model.get("status") == "validated" and model.get("calibration_passed") is True
            result = evaluate(p, row.get("price"), independent_model=True,
                              model_verified=True, event_verified=True,
                              price_verified=bool(row.get("updated_at")),
                              odds_timestamp=row.get("updated_at"), now=now)
            if validated and result["bet_status"] == "BETTING_READY":
                # A positive point estimate is not a validated robust edge.
                result["bet_status"] = "PROVISIONAL"
                result["reason"] = "Model uncertainty and lineup certification unavailable"
                result.pop("expected_value", None)
                result.pop("edge_probability_points", None)
            if not validated and result["model_status"] == "READY":
                result["bet_status"] = "PROVISIONAL"
                result["reason"] = "Independent research projection is not calibrated for betting"
                for field in ("expected_value", "edge_probability_points"):
                    result.pop(field, None)
            decisions.append({"sport": sport, "event_id": row.get("event_id"),
                              "event": row.get("event"), "start_time": row.get("commence_time"),
                              "selection": row.get("selection"), "bookmaker": row.get("bookmaker"),
                              "model_source": model.get("model", model.get("model_version", "independent")),
                              "research_only": not validated, **result})
    return {"generated_at": now.isoformat(), "status": "ok" if decisions else "unavailable",
            "reason": None if decisions else "No verified upcoming independent projections",
            "decisions": decisions}


def main():
    root = Path(__file__).resolve().parents[1]
    snapshots = {}
    for sport, (filename, _) in SPORTS.items():
        try:
            odds = json.loads((root / "feed" / (sport + ".json")).read_text())
            model = json.loads((root / "feed" / filename).read_text())
            snapshots[sport] = (odds, model)
        except (OSError, ValueError):
            continue
    output = build(snapshots)
    target = root / "feed" / "model_market_decisions.json"
    target.write_text(json.dumps(output, indent=2) + "\n")
    print("Published", len(output["decisions"]), "independent market comparisons")


if __name__ == "__main__":
    main()
