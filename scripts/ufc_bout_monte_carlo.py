#!/usr/bin/env python3
"""Reproducible UFC count-prop research simulation. NOT a calibrated betting model."""
import argparse,json,math,random
from pathlib import Path

COUNT_MARKETS=("sig_landed","sig_attempted","takedowns_landed","takedowns_attempted")
def poisson(rng,lam):
    if not math.isfinite(lam) or lam<0:raise ValueError("invalid rate")
    # Sum independent Poisson chunks to avoid tiny exp(-lambda) at high rates.
    total=0
    while lam>0:
        chunk=min(lam,30.0)
        bound=math.exp(-chunk);p=1.;k=0
        while p>bound:
            k+=1;p*=rng.random()
        total+=k-1;lam-=chunk
    return total
def binomial(rng,n,p):
    if not 0<=p<=1:raise ValueError("invalid landing probability")
    return sum(rng.random()<p for _ in range(n))
def simulate(rates,scheduled_rounds,draws=10000,seed=2026,finish_hazard=.18,thresholds=None):
    if scheduled_rounds not in (3,5):raise ValueError("scheduled rounds must be verified 3 or 5")
    if not isinstance(draws,int) or not 100<=draws<=100000:raise ValueError("draws out of bounds")
    if not isinstance(seed,int) or not 0<=seed<2**32:raise ValueError("invalid seed")
    if not 0<=finish_hazard<1:raise ValueError("invalid hazard")
    if set(rates)!=set(COUNT_MARKETS) or any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 or v>500 for v in rates.values()):
        raise ValueError("all four finite nonnegative per-round rates required")
    for landed,attempted in (("sig_landed","sig_attempted"),("takedowns_landed","takedowns_attempted")):
        if rates[landed]>rates[attempted]:raise ValueError("landed rate cannot exceed attempted rate")
    thresholds=thresholds or {}
    if any(k not in COUNT_MARKETS or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for k,v in thresholds.items()):
        raise ValueError("invalid research thresholds")
    rng=random.Random(seed);values={k:[] for k in COUNT_MARKETS};rounds=[]
    for _ in range(draws):
        active=0
        for rd in range(scheduled_rounds):
            active+=1
            if rng.random()<finish_hazard:break
        rounds.append(active)
        # Attempts generate opportunities; landed counts are conditional subsets.
        # Independent landed/attempted Poissons can produce physically impossible fights.
        for landed,attempted in (("sig_landed","sig_attempted"),("takedowns_landed","takedowns_attempted")):
            n=poisson(rng,rates[attempted]*active)
            p=rates[landed]/rates[attempted] if rates[attempted] else 0
            values[attempted].append(n)
            values[landed].append(binomial(rng,n,p))
    out={}
    for key,counts in values.items():
        ordered=sorted(counts)
        out[key]={"mean":sum(counts)/draws,"p10":ordered[int(.10*(draws-1))],
                  "median":ordered[int(.50*(draws-1))],"p90":ordered[int(.90*(draws-1))],
                  "over_threshold_probability":sum(v>thresholds[key] for v in counts)/draws if key in thresholds else None,
                  "threshold":thresholds.get(key)}
    return {"schema_version":1,"model":"illustrative_finish_hazard_plus_poisson",
      "draws":draws,"seed":seed,"scheduled_rounds":scheduled_rounds,"finish_hazard_per_round":finish_hazard,
      "mean_active_rounds":sum(rounds)/draws,"markets":out,
      "assumptions":["constant untrained round-end finish hazard","Poisson attempts with conditional binomial landed counts","no opponent defensive adjustments","no round-partial finish exposure"],
      "point_in_time_certified":False,"calibrated":False,"bet_eligible":False,
      "use_for_live_recommendations":False,"status":"RESEARCH ONLY"}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--rates-json",type=Path,required=True)
    p.add_argument("--rounds",type=int,required=True)
    p.add_argument("--draws",type=int,default=10000)
    p.add_argument("--seed",type=int,default=2026)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=simulate(json.loads(args.rates_json.read_text()),args.rounds,args.draws,args.seed)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
if __name__=="__main__":main()
