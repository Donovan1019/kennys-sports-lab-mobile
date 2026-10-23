#!/usr/bin/env python3
"""Export independently computed, timestamped team ML forecasts from saved inputs.

No odds API calls. This is a baseline scoring model, not a calibrated betting pick.
Reject any game already started and historical inputs dated after forecast time.
"""
import datetime as dt
import json
import math
import pathlib
import re

ROOT=pathlib.Path(__file__).resolve().parents[1]
UTC=dt.timezone.utc
SPORTS={'NFL':'independent_game_inputs.json','NBA':'nba_independent_game_inputs.json','NHL':'nhl_independent_game_inputs.json'}

def stamp(value):
    try:
        result=dt.datetime.fromisoformat(str(value).replace('Z','+00:00'))
        return result.astimezone(UTC) if result.tzinfo else None
    except (ValueError,TypeError):return None

def model(sport,now):
    path=ROOT/'feed'/SPORTS[sport]
    try:data=json.loads(path.read_text())
    except (OSError,ValueError):return []
    predictions=[]
    nhl_history={}
    if sport=='NHL':
        try:nhl_history=json.loads((ROOT/'feed'/'nhl_team_score_history.json').read_text()).get('teams',{})
        except (OSError,ValueError):pass
    for game in data.get('games',[]):
        kickoff=stamp(game.get('commence_time'))
        if not kickoff or kickoff<=now:continue
        teams=game.get('teams',[])
        if sport=='NHL' and (not teams or len(teams)!=2):
            teams=[{'team':name,'score_history':nhl_history.get(name,[])} for name in (game.get('home'),game.get('away'))]
        if not isinstance(teams,list) or len(teams)!=2:continue
        by_name={t.get('team'):t for t in teams if isinstance(t,dict)}
        home=game.get('home');away=game.get('away')
        if home not in by_name or away not in by_name:continue
        h=by_name[home];a=by_name[away]
        if any(not isinstance(t.get('score_history'),list) or len(t['score_history'])< (3 if sport=='NHL' else 10) for t in (h,a)):continue
        # Only use observations that were available before forecast creation.
        histories=[]
        for t in (h,a):
            rows=[r for r in t['score_history'] if stamp(r.get('date')) and stamp(r['date'])<now and isinstance(r.get('scored'),(int,float)) and isinstance(r.get('allowed'),(int,float))]
            if len(rows)<(3 if sport=='NHL' else 10):break
            histories.append(rows[-20:])
        if len(histories)!=2:continue
        def avg(rows,key):return sum(x[key] for x in rows)/len(rows)
        hsc=(avg(histories[0],'scored')+avg(histories[1],'allowed'))/2
        asc=(avg(histories[1],'scored')+avg(histories[0],'allowed'))/2
        # Conservative, explicitly heuristic scoring variance; never labeled calibrated.
        sigma={'NFL':14.0,'NBA':16.0,'NHL':2.3}[sport]
        p_home=0.5*(1+math.erf((hsc-asc)/(sigma*math.sqrt(2))))
        event=game.get('event')
        if not event or not home or not away:continue
        for team,p in ((home,p_home),(away,1-p_home)):
            predictions.append({'event':event,'event_id':game.get('event_id'),
                'commence_time':game['commence_time'],'market':'h2h',
                'selection':team,'model_probability':round(p,6),
                'model_version':'baseline-score-v1-uncalibrated',
                'prediction_created_at':now.isoformat(),
                'model_source':'historical_scoring_only',
                'bet_eligible':False,'research_only':True})
    return predictions

def main():
    now=dt.datetime.now(UTC)
    for sport in SPORTS:
        rows=model(sport,now)
        dest=ROOT/'feed'/(sport.lower()+'_model_predictions.json')
        dest.write_text(json.dumps({'generated_at':now.isoformat(),'sport':sport,
            'model_version':'baseline-score-v1-uncalibrated',
            'predictions':rows,'research_only':True},indent=2)+'\n')
        print(sport,'exported',len(rows),'research-only forecasts')

if __name__=='__main__':main()
