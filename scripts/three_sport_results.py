#!/usr/bin/env python3
"""Fetch completed ESPN game results; never infer missing or live outcomes."""
import argparse
import datetime as dt
import json
import pathlib
import urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[1]
LEAGUES={'NFL':('football','nfl'),'NBA':('basketball','nba'),'NHL':('hockey','nhl')}

def collect(sport,date,fetcher=None):
    group,league=LEAGUES[sport]
    url=f'https://site.api.espn.com/apis/site/v2/sports/{group}/{league}/scoreboard?dates={date.replace("-","")}&limit=100'
    if fetcher is None:
        def fetcher(u):
            request=urllib.request.Request(u,headers={'User-Agent':'KSL-Backtest/1.0'})
            with urllib.request.urlopen(request,timeout=25) as response:
                return json.load(response)
    data=fetcher(url)
    games=[]
    for event in data.get('events',[]):
        status=event.get('status',{}).get('type',{})
        if not status.get('completed'):continue
        for contest in event.get('competitions',[]):
            teams=contest.get('competitors',[])
            if len(teams)!=2:continue
            by_side={x.get('homeAway'):x for x in teams}
            if 'home' not in by_side or 'away' not in by_side:continue
            try:
                home=by_side['home'];away=by_side['away']
                hs=int(home['score']);a_s=int(away['score'])
            except (ValueError,TypeError,KeyError):continue
            games.append({'event_id':str(event.get('id','')),'event':event.get('name'),
                'commence_time':event.get('date'),'home':home.get('team',{}).get('displayName'),
                'away':away.get('team',{}).get('displayName'),'home_score':hs,
                'away_score':a_s,'status':status.get('name'),'completed':True,
                'source':'ESPN scoreboard','source_url':url})
    return {'sport':sport,'date':date,'games':games,'source_url':url}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--date',required=True)
    args=parser.parse_args()
    dt.date.fromisoformat(args.date)
    folder=ROOT/'backtests'/'results'/args.date
    folder.mkdir(parents=True,exist_ok=True)
    for sport in LEAGUES:
        path=folder/(sport.lower()+'.json')
        if path.exists():
            print(sport,'immutable result already exists; skipping')
            continue
        result=collect(sport,args.date)
        if not result['games']:
            print(sport,'no completed games: no empty result file written')
            continue
        path.write_text(json.dumps(result,indent=2)+'\n')
        print(sport,'saved',len(result['games']),'completed games')

if __name__=='__main__':main()
