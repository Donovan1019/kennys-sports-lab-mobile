#!/usr/bin/env python3
"""Append-only NFL/NBA/NHL sportsbook snapshot and conservative settlement audit.

Never interpret saved sportsbook quotes as model picks. A prediction is eligible
only if an independently saved model forecast existed before event start.
"""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
SPORTS={'NFL':'nfl_props.json','NBA':'nba_props.json','NHL':'nhl_props.json'}
UTC=dt.timezone.utc

def stamp(s):
    if not s:return None
    try:return dt.datetime.fromisoformat(str(s).replace('Z','+00:00')).astimezone(UTC)
    except (ValueError,TypeError):return None

def read(path,default=None):
    try:return json.loads(path.read_text())
    except (OSError,ValueError):return default

def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False)

def capture(now):
    day=now.date().isoformat()
    folder=ROOT/'backtests'/'snapshots'/day
    folder.mkdir(parents=True,exist_ok=True)
    report={}
    for sport,file in SPORTS.items():
        source=ROOT/'feed'/file
        data=read(source,{})
        quotes=data.get('odds',[]) if isinstance(data,dict) else []
        good=[];invalid=[]
        for q in quotes:
            if not isinstance(q,dict):continue
            start=stamp(q.get('commence_time'))
            observed=stamp(q.get('updated_at'))
            fetched=stamp(data.get('fetched_at'))
            reasons=[]
            if not start or not observed or not fetched:reasons.append('missing_timestamps')
            if start and (observed and observed>=start or fetched and fetched>=start):reasons.append('not_pregame')
            if observed and observed>now:reasons.append('future_quote_timestamp')
            if fetched and fetched>now:reasons.append('future_feed_timestamp')
            if not all(q.get(k) for k in ('event','market','player','bookmaker')):reasons.append('missing_identity')
            if not isinstance(q.get('price'),(int,float)):reasons.append('missing_price')
            item=dict(q)
            item['audit_flags']=reasons
            (invalid if reasons else good).append(item)
        model_source=read(ROOT/'feed'/(sport.lower()+'_model_predictions.json'),{})\n        model_rows=model_source.get('predictions',[]) if isinstance(model_source,dict) else []\n        model_ok=[]\n        for p in model_rows:\n            if not isinstance(p,dict):continue\n            created=stamp(p.get('prediction_created_at'))\n            start=stamp(p.get('commence_time'))\n            if created and start and created<start and created<=now and p.get('model_version'):\n                model_ok.append(p)\n        payload={'schema':1,'sport':sport,'capture_at':now.isoformat(),
                 'source_file':str(source.relative_to(ROOT)),
                 'source_fetched_at':data.get('fetched_at'),
                 'quotes':good,'rejected_quotes':invalid,
                 'model_predictions':model_ok,
                 'note':'Saved sportsbook quotes are not model predictions. Independently timestamped model predictions are required before kickoff.'}
        payload['sha256']=hashlib.sha256(canonical({k:v for k,v in payload.items() if k!='sha256'}).encode()).hexdigest()
        dest=folder/(sport.lower()+'.json')
        if dest.exists():
            previous=read(dest,{})
            report[sport]={'status':'immutable_existing','eligible_quotes':len(previous.get('quotes',[])),'rejected_quotes':len(previous.get('rejected_quotes',[]))}
        else:
            dest.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n')
            report[sport]={'status':'captured','eligible_quotes':len(good),'rejected_quotes':len(invalid)}
    return report

def grade(date):
    directory=ROOT/'backtests'/'snapshots'/date
    result={'date':date,'generated_at':dt.datetime.now(UTC).isoformat(),'sports':{},'summary':{'verified_picks':0,'wins':0,'losses':0,'pushes':0,'roi':None,'hit_rate':None}}
    for sport in SPORTS:
        snap=read(directory/(sport.lower()+'.json'))
        if not snap:
            result['sports'][sport]={'status':'NO_SNAPSHOT','graded':0}
            continue
        predictions=snap.get('model_predictions',[])
        valid=[];blocked=[]
        for p in predictions:
            event=stamp(p.get('commence_time'))
            created=stamp(p.get('prediction_created_at'))
            if not event or not created or created>=event:blocked.append({'prediction':p,'reason':'NO_VERIFIED_PREGAME_TIMESTAMP'});continue
            if not p.get('model_version') or not p.get('market') or not p.get('selection'):blocked.append({'prediction':p,'reason':'MISSING_MODEL_METADATA'});continue
            valid.append(p)
        # Outcome and sportsbook matching are intentionally not inferred.
        # A separate immutable boxscore/result source is required to settle each pick.
        result['sports'][sport]={'status':'OUTCOMES_UNVERIFIED' if valid else 'NO_VERIFIED_PREGAME_PREDICTIONS',
            'saved_quotes':len(snap.get('quotes',[])),'eligible_predictions':len(valid),
            'blocked_predictions':blocked,'graded':0,'pending':len(valid)}
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('action',choices=['capture','grade'])
    ap.add_argument('--date',help='UTC date YYYY-MM-DD for grading')
    args=ap.parse_args()
    now=dt.datetime.now(UTC)
    if args.action=='capture':result=capture(now)
    else:
        day=args.date or (now-dt.timedelta(days=1)).date().isoformat()
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',day):ap.error('invalid date')
        result=grade(day)
        output=ROOT/'backtests'/'reports'/f'{day}.json'
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
