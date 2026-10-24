"""Out-of-sample UFC model reliability and temporal robustness diagnostics.

Scores are diagnostic research metrics, not betting profitability estimates.
"""
import math
from collections import defaultdict
from scripts.ufc_opponent_walkforward import evaluate

def calibration(predictions, bins=10):
    if not predictions:raise ValueError("empty test predictions")
    groups=defaultdict(list)
    for p,y in predictions:
        if not math.isfinite(p) or not 0<=p<=1 or y not in (0,1):
            raise ValueError("invalid prediction or label")
        groups[min(bins-1,int(p*bins))].append((p,y))
    out=[]
    for idx in range(bins):
        items=groups[idx]
        if not items:continue
        n=len(items)
        mean_p=sum(p for p,_ in items)/n
        observed=sum(y for _,y in items)/n
        # Wilson 95% interval for the observed hit frequency.
        z=1.96
        denom=1+z*z/n
        center=(observed+z*z/(2*n))/denom
        half=z*math.sqrt(observed*(1-observed)/n+z*z/(4*n*n))/denom
        out.append({"bin":idx,"count":n,"mean_probability":mean_p,
                    "observed_win_rate":observed,
                    "wilson_95_low":max(0,center-half),
                    "wilson_95_high":min(1,center+half)})
    ece=sum(x["count"]*abs(x["mean_probability"]-x["observed_win_rate"]) for x in out)/len(predictions)
    return {"bins":out,"expected_calibration_error":ece}

def temporal_robustness(rows):
    if len(rows)<100:raise ValueError("insufficient historical examples")
    folds=[]
    for fraction in (.6,.7,.8):
        score=evaluate(rows,train_fraction=fraction)
        folds.append({k:score[k] for k in ("cutoff_date","training_fights","test_fights","test_brier","test_log_loss","test_accuracy")})
    return {"folds":folds,"research_only":True,
            "warning":"Overlapping test periods; folds are sensitivity checks, not independent confidence intervals. No odds or PIT-certified capture history."}
