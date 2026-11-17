#!/usr/bin/env python3
"""Append-only pregame forecast archive; never manufactures final outcomes."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
MODEL=ROOT/'feed/model_market_decisions.json'
OUT=ROOT/'data/kalshi-pregame-forecasts.json'
def utc(value):
    try:
        d=datetime.fromisoformat(str(value).replace('Z','+00:00'))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (TypeError,ValueError): return None
def collect(now=None):
    now=now or datetime.now(timezone.utc)
    archive={'schema_version':1,'observations':[]}
    if OUT.exists(): archive=json.loads(OUT.read_text())
    else:
        OUT.parent.mkdir(parents=True,exist_ok=True)
        OUT.write_text(json.dumps(archive,indent=2)+'\n')
    if not MODEL.exists():
        print('Model feed missing: empty archive initialized, no forecasts invented')
        return
    model=json.loads(MODEL.read_text())
    generated=utc(model.get('generated_at'))
    if model.get('status')!='ok' or not generated or not (0<=(now-generated).total_seconds()<=86400):
        print('Model feed stale/unavailable: preserving archive without adding forecasts')
        return
    rows=archive.get('observations',[])
    market_path=ROOT/'data/kalshi-markets.json'
    market_rows=json.loads(market_path.read_text()).get('markets',[]) if market_path.exists() else []
    sport_map={'basketball_nba':'nba','americanfootball_nfl':'nfl','icehockey_nhl':'nhl','basketball_ncaab':'ncaab'}
    def norm(value):return re.sub(r'[^a-z0-9]','',str(value or '').lower())
    existing={(r.get('event_id'),r.get('selection'),r.get('model_source'),r.get('forecast_at')) for r in rows}
    added=0
    for r in model.get('decisions',[]):
        start=utc(r.get('start_time'));prob=r.get('model_probability')
        if not start or start<=now or not isinstance(prob,(int,float)) or isinstance(prob,bool) or not 0<prob<1:continue
        if not r.get('event_id') or not r.get('selection') or not r.get('model_source'):continue
        key=(r['event_id'],r['selection'],r['model_source'],model['generated_at'])
        if key in existing:continue
        day=start.astimezone(ZoneInfo('America/New_York')).date().isoformat()
        candidates=[m for m in market_rows if m.get('sport')==sport_map.get(r.get('sport')) and m.get('game_date_et')==day and norm(str(m.get('title','')).removesuffix(' wins'))==norm(r['selection'])]
        # Require exact sport, date and selection, and a single event ticker.
        tickers={m.get('ticker') for m in candidates if m.get('ticker')}
        matched_ticker=next(iter(tickers)) if len(tickers)==1 else None
        rows.append({'kalshi_ticker':matched_ticker,'kalshi_match_status':'UNIQUE' if matched_ticker else 'UNVERIFIED','event_id':r['event_id'],'sport':r.get('sport'),'event':r.get('event'),
                     'selection':r['selection'],'model_source':r['model_source'],
                     'forecast_at':model['generated_at'],'game_start_at':r['start_time'],
                     'predicted_probability':prob,'research_only':bool(r.get('research_only')),
                     'bet_status':r.get('bet_status'),'actual_outcome':None,
                     'settlement_verified':False,'settlement_source':None})
        existing.add(key);added+=1
    archive['observations']=rows
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(archive,indent=2)+'\n')
    print(f'Archived {added} new pregame forecasts; {len(rows)} total; outcomes remain unverified')
if __name__=='__main__':collect()
