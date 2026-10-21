#!/usr/bin/env python3
"""Leakage-resistant walk-forward NBA team win baseline validation."""
import json,math
from collections import defaultdict
from pathlib import Path
games=json.loads(Path('feed/nba_completed_games.json').read_text())['games']
games=sorted((g for g in games if isinstance(g.get('home_score'),(int,float)) and isinstance(g.get('away_score'),(int,float)) and g.get('home') and g.get('away')),key=lambda x:(x['date'],x.get('event_id','')))
history=defaultdict(list)
predictions=[]
for g in games:
    day=g['date'][:10]
    if day<'2025-10-01':continue
    h,a=g['home'],g['away']
    # Only use games strictly before this game date to prevent same-day leakage.
    prior_h=[r for r in history[h] if r[0]<day][-40:]
    prior_a=[r for r in history[a] if r[0]<day][-40:]
    if len(prior_h)>=15 and len(prior_a)>=15:
        # Scores estimated from historical offense and opponent defense.
        def avg(rows,col):return sum(r[col] for r in rows)/len(rows)
        home_mean=(avg(prior_h,1)+avg(prior_a,2))/2+2
        away_mean=(avg(prior_a,1)+avg(prior_h,2))/2
        # Fixed uncertainty, explicitly uncalibrated; logistic margin link.
        prob=1/(1+math.exp(-(home_mean-away_mean)/12))
        prob=max(.02,min(.98,prob))
        outcome=int(g['home_score']>g['away_score'])
        predictions.append({'date':day,'event_id':g.get('event_id'),'home':h,'away':a,'home_win_probability':round(prob,5),'home_won':outcome,'home_score_prediction':round(home_mean,2),'away_score_prediction':round(away_mean,2),'home_score_actual':g['home_score'],'away_score_actual':g['away_score']})
    history[h].append((day,g['home_score'],g['away_score']))
    history[a].append((day,g['away_score'],g['home_score']))
if not predictions:raise SystemExit('No eligible walk-forward samples')
n=len(predictions)
brier=sum((p['home_win_probability']-p['home_won'])**2 for p in predictions)/n
baseline=sum((.5-p['home_won'])**2 for p in predictions)/n
mae=sum((abs(p['home_score_prediction']-p['home_score_actual'])+abs(p['away_score_prediction']-p['away_score_actual']))/2 for p in predictions)/n
bins=[]
for lo in range(0,100,10):
    selected=[p for p in predictions if lo<=p['home_win_probability']*100<(lo+10)]
    if selected:bins.append({'probability_bin':f'{lo}-{lo+10}%','n':len(selected),'mean_predicted':round(sum(p['home_win_probability'] for p in selected)/len(selected),3),'actual_home_win_rate':round(sum(p['home_won'] for p in selected)/len(selected),3)})
# Chronological holdout calibration: fit only on the earlier 70% of games.
# Optimize logistic temperature without using any holdout outcomes.
split=int(n*.70)
# Keep every game from a given date on the same side of the split.
cutoff=predictions[split]['date']
train=[p for p in predictions if p['date']<cutoff]
test=[p for p in predictions if p['date']>=cutoff]
assert len(train)>=200 and len(test)>=200 and train[-1]['date']<test[0]['date']
def score(rows,scale):
    return sum((1/(1+math.exp(-((p['home_score_prediction']-p['away_score_prediction'])/scale)))-p['home_won'])**2 for p in rows)/len(rows)
scales=[x/2 for x in range(6,81)]
best_scale=min(scales,key=lambda scale:score(train,scale))
holdout_brier=score(test,best_scale)
holdout_raw=score(test,12)
holdout_constant=.25
holdout_home_rate=sum(p['home_won'] for p in train)/len(train)
holdout_home_baseline=sum((holdout_home_rate-p['home_won'])**2 for p in test)/len(test)
calibration={'train_games':len(train),'test_games':len(test),'train_end':train[-1]['date'],'test_start':test[0]['date'],'logistic_scale':best_scale,'holdout_brier_calibrated':round(holdout_brier,5),'holdout_brier_fixed_scale':round(holdout_raw,5),'holdout_brier_constant_50pct':holdout_constant,'holdout_brier_historical_home_rate':round(holdout_home_baseline,5),'holdout_pass':holdout_brier<min(holdout_raw,holdout_home_baseline,holdout_constant)}
report={'method':'strict-prior-day-walk-forward','status':'experimental_uncalibrated','samples':n,'date_start':predictions[0]['date'],'date_end':predictions[-1]['date'],'brier':round(brier,5),'constant_50pct_brier':round(baseline,5),'team_score_mae':round(mae,3),'calibration_bins':bins,'chronological_holdout':calibration,'notes':['No closing odds, lineup/injury inputs or bookmaker vig comparison','Fixed logistic scale 12 is not trained or calibrated','Only historical scores strictly prior to game date used']}
Path('feed/nba_backtest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
