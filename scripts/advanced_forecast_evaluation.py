"""Leakage-safe evaluation of immutable pregame forecast outcomes.

Metrics are descriptive, not evidence of a betting edge. All intervals are
Wilson binomial intervals; no synthetic or backfilled forecasts are used.
"""
import json
import math
from pathlib import Path

def wilson_interval(wins, n, z=1.96):
    if not n:
        return None
    p = wins / n
    den = 1 + z*z/n
    center = (p + z*z/(2*n))/den
    half = z*math.sqrt((p*(1-p) + z*z/(4*n))/n)/den
    return [round(max(0, center-half), 6), round(min(1, center+half), 6)]

def evaluate(audit):
    rows = [r for r in audit.get("scored", []) if
            type(r.get("home_probability")) in (int, float) and
            math.isfinite(r["home_probability"]) and
            0 < r["home_probability"] < 1 and
            type(r.get("home_won")) is int and r["home_won"] in (0, 1)]
    n = len(rows)
    if not n:
        return {"status": "awaiting_verified_results", "sample_size": 0,
                "future_or_unmatched_events": audit.get("unmatched_events", 0),
                "edge_claim_allowed": False}
    probabilities = [r["home_probability"] for r in rows]
    outcomes = [r["home_won"] for r in rows]
    brier = sum((p-y)**2 for p,y in zip(probabilities,outcomes))/n
    logloss = -sum(y*math.log(p)+(1-y)*math.log1p(-p)
                   for p,y in zip(probabilities,outcomes))/n
    accuracy = sum((p >= .5) == bool(y) for p,y in zip(probabilities,outcomes))
    mean_p = sum(probabilities)/n
    observed = sum(outcomes)/n
    bins = []
    ece = 0
    for low, high in ((0,.2),(.2,.4),(.4,.6),(.6,.8),(.8,1.000001)):
        group = [(p,y) for p,y in zip(probabilities,outcomes) if low <= p < high]
        if not group:
            continue
        gp = sum(p for p,_ in group)/len(group)
        gy = sum(y for _,y in group)/len(group)
        ece += len(group)/n*abs(gp-gy)
        bins.append({"range": [low,min(1,high)], "n":len(group),
                     "predicted":round(gp,6),"observed":round(gy,6),
                     "observed_wilson_95":wilson_interval(sum(y for _,y in group),len(group))})
    return {"status":"research_only","sample_size":n,
            "brier":round(brier,6),"log_loss":round(logloss,6),
            "classification_accuracy":round(accuracy/n,6),
            "classification_accuracy_wilson_95":wilson_interval(accuracy,n),
            "expected_calibration_error":round(ece,6),
            "mean_home_probability":round(mean_p,6),
            "observed_home_win_rate":round(observed,6),
            "observed_home_win_rate_wilson_95":wilson_interval(sum(outcomes),n),
            "calibration_bins":bins,
            "future_or_unmatched_events":audit.get("unmatched_events",0),
            "edge_claim_allowed":False,
            "warning":"Descriptive in-sample diagnostics only; require independent pregame bookmaker baselines and out-of-sample validation before claims of edge."}

def main():
    for sport in ("basketball_nba","icehockey_nhl","americanfootball_nfl"):
        path = Path(f"feed/{sport}_forecast_outcomes.json")
        if not path.exists():
            print(f"{sport}: evaluation unavailable; missing {path}")
            continue
        result = evaluate(json.loads(path.read_text()))
        Path(f"feed/{sport}_advanced_evaluation.json").write_text(json.dumps(result,indent=2)+"\n")
        print(f"{sport}: advanced evaluation {result['status']}, n={result['sample_size']}")
if __name__ == "__main__":
    main()
