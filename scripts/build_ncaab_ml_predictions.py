#!/usr/bin/env python3
"""Independent NCAA men's basketball ML research model using completed ESPN scores.
No sportsbook prices are used to generate probabilities. Research only, never bet-certified.
"""
import json, math, time, unicodedata, urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def normalize(name):
    s=''.join(c for c in unicodedata.normalize('NFKD',name or '') if not unicodedata.combining(c))
    return ''.join(c for c in s.casefold() if c.isalnum())
def get(day):
    url='https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates='+day+'&limit=500&groups=50'
    req=urllib.request.Request(url,headers={'User-Agent':'KennysSportsLab-NCAAB-Research/1.0'})
    with urllib.request.urlopen(req,timeout=22) as response:return json.load(response)
def build(odds, history, now):
    scores=defaultdict(list)
    for event in sorted(history,key=lambda e:e.get('date','')):
        comp=(event.get('competitions') or [{}])[0]
        if not event.get('status',{}).get('type',{}).get('completed'):continue
        teams=comp.get('competitors') or []
        if len(teams)!=2:continue
        try:
            home=next(t for t in teams if t.get('homeAway')=='home')
            away=next(t for t in teams if t.get('homeAway')=='away')
            hp=float(home['score']);ap=float(away['score'])
            if not all(math.isfinite(x) for x in (hp,ap)):continue
            for t,margin in ((home,hp-ap),(away,ap-hp)):
                names={t.get('team',{}).get(k) for k in ('displayName','shortDisplayName')}
                for name in names:
                    if name:scores[normalize(name)].append((event.get('date',''),margin))
        except (KeyError,ValueError,TypeError,StopIteration):continue
    predictions=[];seen=set()
    for q in odds.get('odds',[]):
        eid=q.get('event_id');event=q.get('event','')
        if q.get('market')!='h2h' or not eid or eid in seen or ' @ ' not in event:continue
        seen.add(eid)
        away,home=event.split(' @ ',1)
        try:tip=datetime.fromisoformat(q['commence_time'].replace('Z','+00:00'))
        except (KeyError,ValueError,AttributeError):continue
        if tip<=now:continue
        # Exclude results on/after tip; only games with verified timestamps enter ratings.
        def rating(team):
            past=[margin for stamp,margin in scores.get(normalize(team),[]) if stamp and datetime.fromisoformat(stamp.replace('Z','+00:00'))<tip]
            if len(past)<3:return None,len(past)
            past=past[-15:]
            return sum(past)/(len(past)+8),len(past)
        ar,an=rating(away);hr,hn=rating(home)
        if ar is None or hr is None:continue
        # Baseline margin-only model, intentionally not calibrated to sportsbook prices.
        p=1/(1+math.exp(-max(-20,min(20,(hr-ar+2.5)/12))))
        for team,prob in ((home,p),(away,1-p)):
            predictions.append({'event_id':eid,'team':team,'win_probability':round(prob,6),'sample_games':hn if team==home else an})
    return {'generated_at':now.isoformat(),'status':'RESEARCH_ONLY' if predictions else 'UNAVAILABLE','model':'independent-score-margin-shrinkage-baseline','source':'ESPN completed NCAA MBB scores, 30-day historical lookback; no bookmaker prices in probability inputs','calibration_status':'UNVERIFIED','lineup_status':'UNVERIFIED','bet_eligible':False,'predictions':predictions}
def main():
    now=datetime.now(timezone.utc)
    odds=json.loads((ROOT/'feed/basketball_ncaab.json').read_text())
    history=[];errors=[]
    for n in range(1,31):
        day=(now-timedelta(days=n)).strftime('%Y%m%d')
        try:history.extend(get(day).get('events',[]))
        except Exception as exc:errors.append(day+':'+type(exc).__name__)
        time.sleep(.04)
    output=build(odds,history,now)
    output['history_events']=len(history)
    output['failed_days']=len(errors)
    if len(history)<30:
        output.update(status='UNAVAILABLE',predictions=[],reason='Insufficient independent historical ESPN games')
    target=ROOT/'feed/ncaab_ml_predictions.json'
    target.write_text(json.dumps(output,indent=2)+'\n')
    print('NCAAB independent research:',output['status'],len(output['predictions']),'predictions;',len(history),'historical events;',len(errors),'failed days')
if __name__=='__main__':main()
