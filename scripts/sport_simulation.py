"""Sport-aware experimental full-game score simulation. No odds used as inputs.
NHL ties are resolved with a simplified overtime/shootout proxy; NOT a validated
regulation/OT pricing model. All results require independent calibration.
"""
import math,random
from scripts.matchup_monte_carlo import simulate_game

def poisson(rng,lam):
    if not isinstance(lam,(int,float)) or not math.isfinite(lam) or lam<0 or lam>20:
        raise ValueError("Invalid goal expectation")
    # Exact Poisson inverse transform for typical hockey scoring rates.
    p=math.exp(-lam);u=rng.random();n=0;c=p
    while u>c:
        n+=1;p*=lam/n;c+=p
    return n

def simulate_sport(sport,away_mean,home_mean,away_sd,home_sd,*,trials=10000,seed=42):
    if sport!="icehockey_nhl":
        return simulate_game(away_mean,home_mean,away_sd,home_sd,trials=trials,seed=seed)
    if type(trials)!=int or not 1000<=trials<=100000:
        raise ValueError("Invalid trial count")
    if any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in (away_mean,home_mean,away_sd,home_sd)):
        raise ValueError("Invalid NHL parameters")
    if min(away_mean,home_mean)<0 or min(away_sd,home_sd)<=0:raise ValueError("Invalid NHL parameters")
    rng=random.Random(seed)
    # Score observations include OT/shootout final goals, so this approximation
    # is not an independent regulation-goals estimator.
    aw=max(.01,away_mean);hm=max(.01,home_mean)
    home_ot=hm/(hm+aw)
    scores=[]
    for _ in range(trials):
        a=poisson(rng,aw);h=poisson(rng,hm)
        if a==h:
            if rng.random()<home_ot:h+=1
            else:a+=1
        scores.append((a,h))
    return scores
