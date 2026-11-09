#!/usr/bin/env python3
"""Independent NHL team goal-rate inputs from completed ESPN scoreboards.
Research only: observed goals are NOT expected-goals shot-quality data.
"""
import json,urllib.request,time
from pathlib import Path
from datetime import datetime,timedelta,timezone
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'KSL-NHL-research/1.0'})
    with urllib.request.urlopen(req,timeout=18) as resp:return json.load(resp)
def main():
    rows=json.loads((ROOT/'feed/icehockey_nhl.json').read_text()).get('odds',[])
    events={r['event_id']:r for r in rows if r.get('event_id') and r.get('market')=='h2h'}
    now=datetime.now(timezone.utc)
    games={}
    errors=[]
    for n in range(1,24):
        day=(now-timedelta(days=n)).strftime('%Y%m%d')
        try:
            data=get('https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates='+day)
            for event in data.get('events',[]):
                comp=(event.get('competitions') or [{}])[0]
                if not event.get('status',{}).get('type',{}).get('completed'):continue
                teams=comp.get('competitors',[])
                if len(teams)!=2:continue
                if any(t.get('score') is None for t in teams):continue
                games[event['id']]=teams
        except Exception as e:errors.append(day+':'+type(e).__name__)
        time.sleep(.08)
    totals=defaultdict(list)
    for teams in games.values():
        for t in teams:
            name=t.get('team',{}).get('displayName')
            if name:totals[name].append(float(t['score']))
    # A modest shrinkage toward a league 3.0 goals/game baseline.
    def rate(team):
        sample=totals.get(team,[])
        if len(sample)<5:return None,len(sample)
        return (sum(sample)+8*3.0)/(len(sample)+8),len(sample)
    output={}
    for eid,e in events.items():
        try:away,home=e['event'].split(' @ ',1)
        except ValueError:continue
        ar,an=rate(away);hr,hn=rate(home)
        if ar is None or hr is None:continue
        output[eid]={'away_xg':round(ar,4),'home_xg':round(hr,4),'updated_at':now.isoformat(),'source_type':'independent','source':'ESPN completed game scores; 23-day lookback; shrinkage to 3.0 goals/game; NOT shot-quality xG','away_games':an,'home_games':hn,'data_quality':'RESEARCH_ONLY_GOALS_PER_GAME'}
    target=ROOT/'feed/nhl_expected_goals.json'
    target.write_text(json.dumps(output,indent=2)+'\n')
    print('NHL historical scores:',len(games),'games;',len(output),'matched projections; failed days:',len(errors))
    if not games:raise SystemExit('No historical games; refusing to replace verified data')
if __name__=='__main__':main()
