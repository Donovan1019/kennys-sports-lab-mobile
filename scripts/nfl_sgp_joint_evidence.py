#!/usr/bin/env python3
"""Evidence-only NFL SGP validation. No synthetic quotes, outcomes, or bet promotion."""
import json
import math
from collections import defaultdict
from pathlib import Path

REQUIRED = ("event_id", "player_id", "market", "line", "side", "forecast_at", "kickoff_at", "outcome", "probability")

def validate(records, quotes=()):
    """Return a fail-closed audit of pregame, game-linked prop observations; holdout remains unverified."""
    issues, grouped, seen = [], defaultdict(list), set()
    for i, r in enumerate(records):
        missing = [k for k in REQUIRED if k not in r or r[k] is None or r[k] == ""]
        if missing:
            issues.append({"row": i, "reason": "missing_fields", "fields": missing})
            continue
        key = (r["event_id"], r["player_id"], r["market"], r["line"], r["side"], r["forecast_at"])
        if key in seen:
            issues.append({"row": i, "reason": "duplicate_forecast"})
            continue
        seen.add(key)
        try:
            from datetime import datetime
            forecast = datetime.fromisoformat(str(r["forecast_at"]).replace("Z", "+00:00"))
            kickoff = datetime.fromisoformat(str(r["kickoff_at"]).replace("Z", "+00:00"))
            p = float(r["probability"])
            line = float(r["line"])
            outcome = float(r["outcome"])
            if forecast.tzinfo is None or kickoff.tzinfo is None or forecast >= kickoff:
                raise ValueError("not a timezone-aware pregame forecast")
            if not (math.isfinite(p) and 0 < p < 1 and math.isfinite(line) and math.isfinite(outcome)):
                raise ValueError("invalid numeric values")
            if r["side"] not in ("over", "under"):
                raise ValueError("invalid side")
        except (ValueError, TypeError, OverflowError):
            issues.append({"row": i, "reason": "invalid_pregame_or_numeric_data"})
            continue
        hit = outcome > line if r["side"] == "over" else outcome < line
        if outcome == line:
            issues.append({"row": i, "reason": "push_requires_separate_settlement"})
            continue
        slip = r.get("slip_id")
        if not isinstance(slip, str) or not slip.strip():
            issues.append({"row": i, "reason": "missing_slip_id_for_joint_evaluation"})
            grouped[(str(r["event_id"]), f"unpaired-row-{i}")].append((p, int(hit)))
        else:
            grouped[(str(r["event_id"]), slip.strip())].append((p, int(hit)))
    multi = [g for g in grouped.values() if len(g) >= 2]
    single_brier = (sum((p-y)**2 for g in grouped.values() for p,y in g) /
                    sum(map(len, grouped.values()))) if grouped else None
    # Independence is a *baseline*, not a valid same-game probability estimate.
    baseline = [math.prod(p for p,_ in g) for g in multi]
    observed = [int(all(y for _,y in g)) for g in multi]
    independent_brier = (sum((p-y)**2 for p,y in zip(baseline,observed))/len(multi)) if multi else None
    quote_rows = list(quotes)
    # Quotes are never considered verified merely because a caller supplies them.
    return {
        "status": "BLOCKED", "betting_eligible": False,
        "event_slip_groups": len(grouped), "events": len({key[0] for key in grouped}), "same_game_multi_leg_events": len(multi),
        "valid_legs": sum(map(len, grouped.values())), "rejected_rows": issues,
        "single_leg_brier": single_brier,
        "independent_joint_baseline_brier": independent_brier,
        "joint_model_brier": None, "joint_model_improvement_verified": False,
        "bookmaker_quotes_supplied_unverified": len(quote_rows),
        "verified_actual_sgp_bookmaker_quote": False,
        "same_game_sgp_expected_value_validated": False,
        "forward_holdout_verified": False,
        "limitations": "No joint model, forward holdout, authenticated bookmaker quote, roster verification or verified EV. Only explicitly slip-linked observations are joined; independence baseline remains diagnostic only."
    }

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--observations", required=True, type=Path)
    parser.add_argument("--quotes", type=Path)
    args = parser.parse_args()
    observations = json.loads(args.observations.read_text())
    quotes = json.loads(args.quotes.read_text()) if args.quotes else []
    if not isinstance(observations, list) or not isinstance(quotes, list):
        raise SystemExit("Expected JSON arrays")
    print(json.dumps(validate(observations, quotes), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
