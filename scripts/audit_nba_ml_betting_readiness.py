#!/usr/bin/env python3
"""Evidence-aware, fail-closed NBA ML betting-readiness audit."""
import datetime as dt
import json
import pathlib

EVIDENCE_CHECKS = {
    "historical_pregame_odds_backtest": ("historical_pregame_odds_backtest_verified", "outcome_market"),
    "closing_line_value_verified": ("closing_line_value_verified", "outcome_market"),
    "injury_lineup_rest_confirmed": ("injury_lineup_rest_confirmed", "availability"),
    "executable_same_book_parlay_quote": ("executable_same_book_parlay_quote", "parlay_quotes"),
    "correlation_stress_test_verified": ("correlation_stress_test_verified", "correlation"),
}

def audit(odds, model, now, schedule=None, archive=None, evidence=None):
    report = {"status": "not_bet_eligible", "checked_at": now.isoformat(), "checks": {}}
    checks = report["checks"]
    def fresh(obj, key):
        try:
            stamp = dt.datetime.fromisoformat(obj[key].replace("Z", "+00:00"))
            return stamp.tzinfo is not None and 0 <= (now - stamp).total_seconds() <= 150 * 60
        except (ValueError, TypeError, KeyError, AttributeError):
            return False

    checks["odds_fresh"] = odds.get("status") == "ok" and fresh(odds, "fetched_at")
    checks["model_fresh_and_calibrated"] = model.get("status") == "validated" and model.get("calibration_passed") is True and fresh(model, "generated_at")
    schedule, archive = schedule or {}, archive or {}
    checks["schedule_evidence_fresh"] = schedule.get("status") == "ok" and fresh(schedule, "fetched_at")
    checks["pregame_odds_archiving_active"] = archive.get("status") == "ok" and fresh(archive, "captured_at") and len(archive.get("rows", [])) > 0

    # Existing research outputs must never be silently promoted to certified bets.
    # A future dedicated verification pipeline may provide independently audited
    # records; research-only, stale or missing records are explicitly rejected.
    evidence = evidence or {}
    details = {}
    for name, (field, source) in EVIDENCE_CHECKS.items():
        item = evidence.get(source, {})
        verified = (
            item.get("status") == "verified"
            and item.get(field) is True
            and fresh(item, "verified_at")
            and isinstance(item.get("verification_id"), str)
            and bool(item["verification_id"].strip())
        )
        checks[name] = verified
        details[name] = {
            "status": "PASS" if verified else "UNVERIFIED",
            "source": source,
            "reason": "Independent, current verification present" if verified else (
                "Research-only evidence is not certification" if item.get("status") == "research_only"
                else "No current independent verification record"
            ),
        }
    market = evidence.get("outcome_market", {})
    roi = market.get("paper_roi")
    sample = market.get("paper_selected_events")
    if (market.get("status") == "research_only"
            and isinstance(roi, (int, float)) and not isinstance(roi, bool)
            and isinstance(sample, int) and not isinstance(sample, bool) and sample > 0):
        report["research_warning"] = {
            "status": "RESEARCH_ONLY",
            "paper_roi": roi,
            "paper_selected_events": sample,
            "reason": "Retrospective paper returns are not executed bets or a validated forward test; investigate negative performance before certification."
        }
    report["check_details"] = details
    missing = [name for name, passed in checks.items() if not passed]
    report["outstanding_checks"] = missing
    report["reason"] = "Unverified: " + ", ".join(missing) if missing else "All evidence checks passed"
    # Keep the explicit betting promotion disabled pending a separately reviewed,
    # executable end-to-end certification process.
    return report

def main():
    def load(path):
        try:
            return json.loads(pathlib.Path(path).read_text())
        except (OSError, ValueError):
            return {}
    archive_root = pathlib.Path("data/nba_ml_odds_archive")
    archives = sorted(archive_root.glob("*/*.json")) if archive_root.exists() else []
    latest_archive = load(archives[-1]) if archives else {}
    evidence = {"outcome_market": load("feed/nba_ml_outcome_market_audit.json")}
    report = audit(load("feed/basketball_nba.json"), load("feed/nba_ml_predictions.json"),
                   dt.datetime.now(dt.timezone.utc), load("feed/nba_ml_schedule_evidence.json"),
                   latest_archive, evidence)
    target = pathlib.Path("feed/nba_ml_betting_readiness.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n")
    print("NBA ML betting readiness:", report["status"], report["outstanding_checks"])

if __name__ == "__main__":
    main()
