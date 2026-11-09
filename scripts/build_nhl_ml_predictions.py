#!/usr/bin/env python3
"""Publish NHL moneyline research projections only when independent scoring inputs exist.
Never transform sportsbook prices into fake model predictions.
"""
import json,math,sys
from datetime import datetime,timezone
from pathlib import Path
from nhl_moneyline_model import home_moneyline_probability
ROOT=Path(__file__).resolve().parents[1]
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
            status='RESEARCH_ONLY'
        else:p=None;status='UNAVAILABLE'
        out.append({'event_id':eid,'event':r.get('event'),'commence_time':r.get('commence_time'),'status':status,'home_win_probability':p,'away_win_probability':None if p is None else 1-p,'goalie_status':'UNVERIFIED','simulation_status':'UNAVAILABLE','source':item.get('source') if valid else None})
    target=ROOT/'feed/nhl_ml_predictions.json'
    target.write_text(json.dumps({'generated_at':datetime.now(timezone.utc).isoformat(),'model':'independent-poisson-research-baseline','status':'RESEARCH_ONLY','predictions':out},indent=2)+'\n')
    print('NHL research feed: %s games, %s independent inputs'%(len(out),sum(x['home_win_probability'] is not None for x in out)))
if __name__=='__main__':main()
