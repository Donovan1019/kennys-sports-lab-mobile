#!/usr/bin/env python3
"""Produce evidence-checked Kalshi advanced picks; never promote baselines."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(path):
    try: return json.loads((ROOT/path).read_text())
    except (OSError,ValueError): return {}
def iso(value):
    try: return datetime.fromisoformat(str(value).replace('Z','+00:00'))
    except (ValueError,TypeError): return None
def eligible(row, now):
    if not isinstance(row,dict): return False
    start=iso(row.get('start_time'))
    if not start or start<=now: return False
    if row.get('research_only') is True: return False
    if row.get('model_tier')!='ADVANCED': return False
    if not all(row.get(key) is True for key in ('simulation_verified','matchup_verified','injury_verified','lineup_verified','calibration_verified')): return False
    evidence=row.get('advanced_evidence')
    if not isinstance(evidence,dict): return False
    if not isinstance(evidence.get('simulation'),dict) or not isinstance(evidence.get('feature_sources'),list): return False
    if not evidence['feature_sources'] or not isinstance(evidence.get('calibration'),dict): return False
    p=row.get('model_probability')
    return isinstance(p,(int,float)) and not isinstance(p,bool) and 0<p<1
def build(now=None):
    now=now or datetime.now(timezone.utc)
    models=read('feed/model_market_decisions.json')
    market=read('data/kalshi-markets.json')
    eligible_rows=[r for r in models.get('decisions',[]) if eligible(r,now)]
    # Actual event/contract matching must be verified independently; never issue a pick
    # merely because a model row self-asserts eligibility.
    return {'generated_at':now.isoformat(),'schema_version':1,
            'status':'AWAITING_VERIFIED_ADVANCED_EVIDENCE' if not eligible_rows else 'AWAITING_VERIFIED_CONTRACT_MATCH',
            'model_feed_generated_at':models.get('generated_at'),
            'market_snapshot_at':market.get('fetched_at'),
            'advanced_evidence_rows':len(eligible_rows),
            'picks':[],
            'reason':'No picks until independently validated advanced evidence, unique contract mapping, settlement terms, and executable prices are available'}
if __name__=='__main__':
    out=build()
    target=ROOT/'data/kalshi-advanced-picks.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'advanced_evidence_rows':out['advanced_evidence_rows'],'picks':len(out['picks'])}))
