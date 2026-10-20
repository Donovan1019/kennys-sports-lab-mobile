"""League-agnostic observed-stat analytics. Never treats historical frequencies as forecasts."""
import math
import random
from statistics import mean, pstdev

def analyze(values, threshold, *, inclusive=True, trials=10000, seed=19):
    if not isinstance(values,(list,tuple)) or not values:
        raise ValueError("Nonempty verified observations required")
    if not math.isfinite(float(threshold)) or float(threshold)<0:
        raise ValueError("Invalid threshold")
    if not 1<=trials<=100000:
        raise ValueError("Invalid trial count")
    v=[float(x) for x in values]
    if any(not math.isfinite(x) or x<0 for x in v):
        raise ValueError("Invalid observation")
    hit=lambda x:x>=threshold if inclusive else x>threshold
    n=len(v); k=sum(hit(x) for x in v); p=k/n
    z=1.96; d=1+z*z/n
    center=(p+z*z/(2*n))/d
    radius=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    rng=random.Random(seed)
    # Resampling historical observations; this is NOT a next-game model.
    resamples=[v[rng.randrange(n)] for _ in range(trials)]
    return {"sample_size":n,"hits":k,"historical_rate":p,
            "wilson_95":[max(0,center-radius),min(1,center+radius)],
            "average":mean(v),"population_std":pstdev(v),
            "historical_resampling_rate":sum(hit(x) for x in resamples)/trials,
            "trials":trials,"is_forecast":False}

def american_break_even(odds):
    if not isinstance(odds,(int,float)) or not math.isfinite(odds) or -100<odds<100:
        raise ValueError("Invalid American odds")
    return (-odds/(-odds+100)) if odds<0 else 100/(odds+100)

def no_vig_two_way(odds_a,odds_b):
    a,b=american_break_even(odds_a),american_break_even(odds_b)
    return a/(a+b),b/(a+b)
