#!/usr/bin/env python3
"""Build independent sport-model vs Kalshi contract comparison feed, fail closed on unmatched events."""
import json,math,re
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
def read(path):
    try:return json.loads((ROOT/path).read_text())
    except (OSError,ValueError):return {}
def dt(x):
    try:return datetime.fromisoformat(str(x).replace('Z','+00:00'))
    except (ValueError,TypeError):return None
def norm(x):return re.sub('[^a-z0-9]','',str(x).lower()).replace('state','st')
def team_match(a,b):
    a,b=norm(a),norm(b)
    return bool(a and b and (a==b or len(b)>=4 and a.startswith(b)))
def fee(price):return math.ceil((0.07*price*(1-price))*100-1e-9)/100
def build(now=None):
    now=now or datetime.now(timezone.utc)
    markets=read('data/kalshi-markets.json')
    decisions=read('feed/model_market_decisions.json')
    nba=read('feed/nba_ml_predictions.json')
    market_at=dt(markets.get('fetched_at')); model_at=dt(decisions.get('generated_at'))
    if not market_at or not model_at or not 0<=(now-market_at).total_seconds()<=3600 or not 0<=(now-model_at).total_seconds()<=86400:
        return {'generated_at':now.isoformat(),'status':'STALE_INPUTS','picks':[],'reason':'Kalshi quote or independent model snapshot stale'}
    groups={}
    for m in markets.get('markets',[]):
        if m.get('status') not in ('active','open') or not m.get('event_ticker') or not re.search(r' wins$',str(m.get('title','')),re.I):continue
        groups.setdefault(m['event_ticker'],[]).append(m)
    models={}
    for d in decisions.get('decisions',[]):
        if d.get('sport') not in ('basketball_nba','americanfootball_nfl','icehockey_nhl','basketball_ncaab'):continue
        start=dt(d.get('start_time'))
        if not start or start<=now:continue
        p=d.get('model_probability')
        if not isinstance(p,(float,int)) or isinstance(p,bool) or not 0<p<1:continue
        key=(d['sport'],d.get('event'),d.get('selection'),d.get('start_time'))
        models[key]=d
    sport_map={'nba':'basketball_nba','nfl':'americanfootball_nfl','nhl':'icehockey_nhl','ncaab':'basketball_ncaab'}
    result={}
    for event,contracts in groups.items():
        if len(contracts)!=2:continue
        sport=contracts[0].get('sport')
        if any(c.get('sport')!=sport for c in contracts):continue
        day=contracts[0].get('game_date_et')
        if not day:continue
        names=[str(c['title'])[:-5].strip() for c in contracts]
        for d in models.values():
            if d['sport']!=sport_map.get(sport):continue
            teams=re.split(r'\s+@\s+',str(d.get('event','')))
            if len(teams)!=2 or not all(any(team_match(t,n) for t in teams) for n in names):continue
            if not team_match(d.get('selection'),names[0]) and not team_match(d.get('selection'),names[1]):continue
            if dt(d['start_time']).astimezone(ZoneInfo('America/New_York')).date().isoformat()!=day:continue
            selected=next((i for i,n in enumerate(names) if team_match(d.get('selection'),n)),None)
            if selected is None:continue
            # Preserve canonical team names from the independent fixture, never truncated contract titles.
            canonical=[]
            for name in names:
                matches=[t for t in teams if team_match(t,name)]
                if len(matches)!=1:break
                canonical.append(matches[0])
            if len(canonical)!=2 or len(set(canonical))!=2:continue
            # The selected model team has probability p; its opponent has 1-p.
            p=float(d['model_probability'])
            for index,c in enumerate(contracts):
                for side,prob in (('YES',p if index==selected else 1-p),('NO',1-p if index==selected else p)):
                    if prob<0.5:continue
                    raw=c.get(('yes_ask' if side=='YES' else 'no_ask')+'_dollars')
                    if raw is None:continue
                    try:ask=float(raw)
                    except (TypeError,ValueError):continue
                    if not 0<ask<1:continue
                    winner=canonical[index] if side=='YES' else canonical[1-index]
                    # No advanced certification without verified sport-specific simulation, lineup and matchup evidence.
                    calibrated=sport=='nba' and nba.get('calibration_passed') is True
                    tier='VALIDATED_BASELINE' if calibrated else 'RESEARCH_BASELINE'
                    f=fee(ask);net=prob-ask-f
                    item={'sport':sport,'event':d['event'],'event_ticker':event,'ticker':c['ticker'],'winner':winner,'side':side,'model_probability':round(prob,6),'kalshi_ask':ask,'estimated_fee':f,'net_ev':round(net,6),'tier':tier,'verified':False,'contract_verified':True,'simulation_verified':False,'quote_at':markets['fetched_at'],'start_time':d['start_time'],'model_source':d.get('model_source'),'explanation':'Independent '+str(d.get('model_source'))+' projection; '+('historical NBA calibration reported, but no lineup/matchup verification' if calibrated else 'uncalibrated research projection')+'. Order-specific fees and depth not verified.'}
                    key=(sport,event,norm(winner))
                    old=result.get(key)
                    if old is None or item['net_ev']>old['net_ev']:result[key]=item
    picks=sorted(result.values(),key=lambda x:(-x['model_probability'],-x['net_ev']))
    return {'generated_at':now.isoformat(),'schema_version':2,'status':'MODEL_COMPARISONS_AVAILABLE' if picks else 'NO_MATCHED_MODEL_COMPARISONS','advanced_count':0,'comparison_count':len(picks),'picks':picks[:150],'reason':'Comparisons are research-grade until sport-specific advanced evidence and order-specific fees are verified'}
if __name__=='__main__':
    out=build();target=ROOT/'data/kalshi-advanced-picks.json';target.parent.mkdir(exist_ok=True,parents=True);target.write_text(json.dumps(out,indent=2)+'\n')
    print(out['status'],len(out['picks']))
