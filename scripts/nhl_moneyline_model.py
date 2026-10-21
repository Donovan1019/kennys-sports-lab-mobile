"""Exact independent-Poisson NHL moneyline baseline, including a tie-resolution proxy.

This is a research model. OT/shootout strength is not independently learned.
Final scores include OT/SO goals, so input scoring rates need further validation.
"""
import math

def poisson_pmf(lam,k):
    return math.exp(-lam+k*math.log(lam)-math.lgamma(k+1)) if lam>0 else (1.0 if k==0 else 0.0)

def home_moneyline_probability(away_goals,home_goals,max_goals=35):
    if not all(isinstance(x,(int,float)) and math.isfinite(x) and 0<x<=12 for x in (away_goals,home_goals)):
        raise ValueError("Invalid NHL expected goals")
    if not isinstance(max_goals,int) or max_goals<20:
        raise ValueError("Invalid truncation")
    a=[poisson_pmf(away_goals,k) for k in range(max_goals+1)]
    h=[poisson_pmf(home_goals,k) for k in range(max_goals+1)]
    outright=sum(h[i]*sum(a[:i]) for i in range(len(h)))
    tied=sum(h[i]*a[i] for i in range(len(h)))
    # Proxy only: tied games resolved proportionally to estimated goal rates.
    p=(outright+tied*home_goals/(home_goals+away_goals))
    mass=sum(a)*sum(h)
    return min(1,max(0,p/mass))
