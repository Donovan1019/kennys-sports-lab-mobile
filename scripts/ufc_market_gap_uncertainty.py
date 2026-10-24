"""Paired, event-date-clustered bootstrap for UFC model vs closing market.

Bootstrap uses deterministic seed, samples dates (not fights) to account for
within-card correlation, and reports uncertainty around model-market error.
"""
import math,random
from collections import defaultdict

def cluster_bootstrap(paired,iterations=2000,seed=20261024):
    if not paired:raise ValueError("empty paired predictions")
    grouped=defaultdict(list)
    for model,market,y,day in paired:
        if not (0<model<1 and 0<market<1 and y in (0,1)):
            raise ValueError("invalid paired probability/label")
        grouped[day].append((model-y)**2-(market-y)**2)
    dates=sorted(grouped)
    if len(dates)<2:raise ValueError("at least two event dates required")
    rng=random.Random(seed)
    vals=[]
    for _ in range(iterations):
        selected=[rng.choice(dates) for _ in dates]
        scores=[v for day in selected for v in grouped[day]]
        vals.append(sum(scores)/len(scores))
    vals.sort()
    point=sum(v for values in grouped.values() for v in values)/len(paired)
    return {"model_minus_market_brier":point,
            "bootstrap_95_low":vals[int(.025*iterations)],
            "bootstrap_95_high":vals[min(iterations-1,int(.975*iterations))],
            "event_days":len(dates),"bootstrap_iterations":iterations,
            "market_advantage_significant_95pct":vals[int(.025*iterations)]>0,
            "model_advantage_significant_95pct":vals[min(iterations-1,int(.975*iterations))]<0,
            "interpretation":"Positive values favor closing market; retrospective closing benchmark, not ROI."}
