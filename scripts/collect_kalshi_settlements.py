#!/usr/bin/env python3
"""Read-only Kalshi settled market evidence; never infer settlement from scores."""
import json
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/kalshi-settlements.json'
SERIES=['KXNBAGAME','KXNFLGAME','KXNHLGAME','KXNCAAMBGAME','KXNCAABGAME']
BASE='https://external-api.kalshi.com/trade-api/v2/markets'
def collect():
 prior={'schema_version':1,'settlements':{}}
 if OUT.exists():prior=json.loads(OUT.read_text())
 found=prior.get('settlements',{})
 errors=[]
 for series in SERIES:
  cursor=None
  for _ in range(3):
   params={'series_ticker':series,'status':'settled','limit':200}
   if cursor:params['cursor']=cursor
   try:
    req=Request(BASE+'?'+urlencode(params),headers={'User-Agent':'KennysSportsLab-ReadOnly/1.0','Accept':'application/json'})
    with urlopen(req,timeout=18) as response:payload=json.load(response)
   except Exception as exc:
    errors.append(series+': '+type(exc).__name__);break
   for m in payload.get('markets') or []:
    ticker=m.get('ticker')
    result=m.get('result')
    if not ticker or result not in ('yes','no'):continue
    found[ticker]={'ticker':ticker,'event_ticker':m.get('event_ticker'),
      'title':m.get('title'),'result':result,'status':m.get('status'),
      'close_time':m.get('close_time'),'source':'Kalshi public settled market API'}
   cursor=payload.get('cursor')
   if not cursor:break
 if errors:print('Settlement API partial failures: '+'; '.join(errors))
 prior['settlements']=found
 prior['last_checked_at']=datetime.now(timezone.utc).isoformat()
 prior['partial_failure']=bool(errors)
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(prior,indent=2)+'\n')
 print('Verified Kalshi settled market records: '+str(len(found)))
if __name__=='__main__':collect()
