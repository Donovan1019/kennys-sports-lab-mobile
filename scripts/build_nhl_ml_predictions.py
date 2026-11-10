#!/usr/bin/env python3
"""Publish NHL moneyline research projections only when independent scoring inputs exist.
Never transform sportsbook prices into fake model predictions.
"""
import json,math,sys,random
from datetime import datetime,timezone
from pathlib import Path
from nhl_moneyline_model import home_moneyline_probability
ROOT=Path(__file__).resolve().parents[1]
def simulate(away,home,seed,n=20000):
    rng=random.Random(seed)
    def pois(rate):
        cutoff=math.exp(-rate); p=1.0; k=0
        while p>cutoff:
            k+=1;p*=rng.random()
        return k-1
    wins=0
    for _ in range(n):
        a,h=pois(away),pois(home)
        wins+=int(h>a or (h==a and rng.random()<home/(away+home)))
    p=wins/n
    return p,math.sqrt(p*(1-p)/n),n

def main():
    odds=json.loads((ROOT/'feed/icehockey_nhl.json').read_text()).get('odds',[])
    src=ROOT/'feed/nhl_expected_goals.json'
    inputs=json.loads(src.read_text()) if src.exists() else {}
    games={}
    for r in odds:
        if r.get('market')!='h2h' or not r.get('event_id'):continue
        games[r['event_id']]=r
    out=[]
    for eid,r in games.items():
        item=inputs.get(eid,{})
        away,home=item.get('away_xg'),item.get('home_xg')
        stamp=item.get('updated_at')
        try:
            updated=datetime.fromisoformat(stamp.replace('Z','+00:00'))
            fresh=(datetime.now(timezone.utc)-updated).total_seconds()<=86400
            valid=fresh and all(isinstance(x,(int,float)) and math.isfinite(x) and 0<x<=12 for x in (away,home)) and item.get('source_type')=='independent'
        except (TypeError,ValueError,AttributeError):valid=False
        if valid:
            p=home_moneyline_probability(away,home)
            sim_p,sim_se,sim_n=simulate(away,home,int(eid[:8],16) if all(c in '0123456789abcdef' for c in eid[:8].lower()) else sum(map(ord,eid)))
            status='RESEARCH_ONLY'
        else:p=None;status='UNAVAILABLE';sim_p=None;sim_se=None;sim_n=0
        out.append({'event_id':eid,'event':r.get('event'),'commence_time':r.get('commence_time'),'status':status,'home_win_probability':p,'away_win_probability':None if p is None else 1-p,'goalie_status':'UNVERIFIED','simulation_status':'RESEARCH_ONLY' if sim_n else 'UNAVAILABLE','simulation_home_probability':sim_p,'simulation_standard_error':sim_se,'simulation_iterations':sim_n,'simulation_model_gap':None if sim_p is None else abs(sim_p-p),'calibration_status':'UNVERIFIED','goalie_impact_status':'UNAVAILABLE','source':item.get('source') if valid else None,'data_quality':item.get('data_quality') if valid else None,'away_sample_games':item.get('away_games') if valid else None,'home_sample_games':item.get('home_games') if valid else None})
    target=ROOT/'feed/nhl_ml_predictions.json'
    target.write_text(json.dumps({'generated_at':datetime.now(timezone.utc).isoformat(),'model':'independent-poisson-research-baseline','status':'RESEARCH_ONLY','predictions':out},indent=2)+'\n')
    print('NHL research feed: %s games, %s independent inputs'%(len(out),sum(x['home_win_probability'] is not None for x in out)))
if __name__=='__main__':main()
