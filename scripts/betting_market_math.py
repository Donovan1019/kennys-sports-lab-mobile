"""Pure betting-market math; no claim of edge without a calibrated model."""
import math

def american_to_decimal(odds):
    if not isinstance(odds,(int,float)) or not math.isfinite(odds) or -100<odds<100:
        raise ValueError("Invalid American odds")
    return 1+odds/100 if odds>0 else 1+100/abs(odds)

def implied_probability(odds):
    return 1/american_to_decimal(odds)

def no_vig_two_way(odds_a,odds_b):
    a,b=implied_probability(odds_a),implied_probability(odds_b)
    return a/(a+b),b/(a+b)

def expected_roi(probability,odds):
    if not 0<=probability<=1 or not math.isfinite(probability):
        raise ValueError("Probability must be between 0 and 1")
    return probability*american_to_decimal(odds)-1

def fractional_kelly(probability,odds,fraction=0.25,cap=0.01):
    if not 0<=fraction<=1 or not 0<=cap<=1:
        raise ValueError("Invalid risk controls")
    net=american_to_decimal(odds)-1
    raw=(probability*(net+1)-1)/net
    return min(cap,max(0,raw*fraction))
