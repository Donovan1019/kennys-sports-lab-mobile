#!/usr/bin/env python3
"""Append-only pregame forecast archive; never manufactures final outcomes."""
import json
from datetime import datetime, timezone
from pathlib import Path

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
    model=json.loads(MODEL.read_text())
    generated=utc(model.get('generated_at'))
    if model.get('status')!='ok' or not generated or not (0<=(now-generated).total_seconds()<=86400):
        raise ValueError('Model feed not fresh: preserving archive')
    archive={'schema_version':1,'observations':[]}
    if OUT.exists(): archive=json.loads(OUT.read_text())
    rows=archive.get('observations',[])
    existing={(r.get('event_id'),r.get('selection'),r.get('model_source'),r.get('forecast_at')) for r in rows}
    added=0
    for r in model.get('decisions',[]):
        start=utc(r.get('start_time'));prob=r.get('model_probability')
        if not start or start<=now or not isinstance(prob,(int,float)) or isinstance(prob,bool) or not 0<prob<1:continue
        if not r.get('event_id') or not r.get('selection') or not r.get('model_source'):continue
        key=(r['event_id'],r['selection'],r['model_source'],model['generated_at'])
        if key in existing:continue
        rows.append({'event_id':r['event_id'],'sport':r.get('sport'),'event':r.get('event'),
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
