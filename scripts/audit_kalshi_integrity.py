#!/usr/bin/env python3
"""Fail-closed audit of Kalshi/model inputs; no fabricated calibration."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(path):
    try: return json.loads((ROOT/path).read_text())
    except (OSError, ValueError): return None
def timestamp(value):
    try: return datetime.fromisoformat(value.replace('Z','+00:00'))
    except (ValueError, AttributeError): return None

def audit(now=None):
    now=now or datetime.now(timezone.utc)
    markets=read('data/kalshi-markets.json') or {}
    models=read('feed/model_market_decisions.json') or {}
    market_time=timestamp(markets.get('fetched_at'))
    model_time=timestamp(models.get('generated_at'))
    market_fresh=bool(market_time and 0 <= (now-market_time).total_seconds() <= 3600)
    model_fresh=bool(model_time and 0 <= (now-model_time).total_seconds() <= 86400)
    model_rows=models.get('decisions') or []
    research_only=sum(1 for r in model_rows if r.get('research_only') or r.get('bet_status')!='BETTING_READY')
    # Calibration needs immutable, timestamped pregame forecasts joined to independently
    # verified final outcomes. A current projections feed is NOT historical evidence.
    archive=read('feed/kalshi_calibration_history.json')
    valid_history=[]
    if isinstance(archive,dict):
        for r in archive.get('observations',[]):
            if (isinstance(r,dict) and isinstance(r.get('predicted_probability'),(float,int))
                and 0<r['predicted_probability']<1 and r.get('actual_outcome') in (0,1)
                and r.get('settlement_verified') is True and r.get('pregame_timestamp_verified') is True
                and r.get('unique_event_match_verified') is True):
                valid_history.append(r)
    brier=sum((r['predicted_probability']-r['actual_outcome'])**2 for r in valid_history)/len(valid_history) if valid_history else None
    # A small history is descriptive only; do not promote to calibrated status.
    calibrated=len(valid_history)>=200 and brier is not None and brier<0.25
    return {'generated_at':now.isoformat(),'status':'BLOCKED' if not calibrated else 'REVIEW_REQUIRED',
      'kalshi_snapshot_fresh':market_fresh,'model_feed_fresh':model_fresh,
      'market_count':len(markets.get('markets') or []),'model_decision_count':len(model_rows),
      'research_only_decisions':research_only,'verified_historical_outcomes':len(valid_history),
      'historical_brier_score':brier,'calibration_passed':calibrated,
      'settlement_verification':'UNAVAILABLE' if not valid_history else 'HISTORICAL_VERIFIED_ONLY',
      'contract_fee_validation':'UNAVAILABLE — series-specific fee/order preview not verified',
      'end_to_end_live_test':'UNVERIFIED — CI audit is not a live browser test',
      'diamond_issuance':'BLOCKED',
      'reasons':['Require 200+ independently verified timestamped historical observations and calibration evaluation',
                 'Require event settlement and order-specific fee validation before any actionable pick',
                 'Require successful live mobile browser and quote-matching test']}
if __name__=='__main__':
    out=audit()
    target=ROOT/'data/kalshi-integrity.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
