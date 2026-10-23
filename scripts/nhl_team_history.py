#!/usr/bin/env python3
"""Build NHL team scoring history from public completed ESPN scoreboards.

Refresh at most once per UTC day; no paid odds calls. Never use current/future games.
"""
import datetime as dt
import json
import pathlib
import urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
UTC=dt.timezone.utc

def generate(now,fetcher=None,days=24):
    if fetcher is None:
        def fetcher(url):
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'KSL-Research/1.0'}),timeout=20) as response:
                return json.load(response)
    history={}
    errors=[]
    for offset in range(1,days+1):
        day=(now-dt.timedelta(days=offset)).date().strftime('%Y%m%d')
        url='https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates='+day+'&limit=100'
        try:data=fetcher(url)
        except Exception as exc:
            errors.append({'date':day,'error':type(exc).__name__})
            continue
        for event in data.get('events',[]):
            when=event.get('date')
            try:
                start=dt.datetime.fromisoformat(when.replace('Z','+00:00'))
                if start>=now:continue
            except (AttributeError,ValueError,TypeError):continue
            if not event.get('status',{}).get('type',{}).get('completed'):continue
            for contest in event.get('competitions',[]):
                teams=contest.get('competitors',[])
                if len(teams)!=2:continue
                try:
                    first,second=teams
                    for t,opp in ((first,second),(second,first)):
                        name=t['team']['displayName']
                        row={'date':when,'game_id':str(event.get('id','')),
                            'scored':int(t['score']),'allowed':int(opp['score'])}
                        history.setdefault(name,{})[row['game_id']]=row
                except (KeyError,ValueError,TypeError):continue
    return {'generated_at':now.isoformat(),'source':'ESPN completed NHL scoreboards',
            'teams':{name:sorted(rows.values(),key=lambda r:r['date']) for name,rows in history.items()},
            'errors':errors}

def main():
    now=dt.datetime.now(UTC)
    dest=ROOT/'feed'/'nhl_team_score_history.json'
    if dest.exists():
        try:
            old=json.loads(dest.read_text())
            updated=dt.datetime.fromisoformat(old['generated_at'].replace('Z','+00:00'))
            if dt.timedelta(0)<=now-updated<dt.timedelta(hours=20):
                print('NHL history cached; skip network')
                return
        except (ValueError,KeyError,TypeError):pass
    result=generate(now)
    if not result['teams']:
        raise RuntimeError('No NHL history returned; preserving existing cache')
    dest.write_text(json.dumps(result,indent=2)+'\n')
    print('NHL history refreshed for',len(result['teams']),'teams;',len(result['errors']),'date errors')

if __name__=='__main__':main()
