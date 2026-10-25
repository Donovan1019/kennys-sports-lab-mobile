#!/usr/bin/env python3
"""Build observed NFL opponent defensive splits from ESPN completed-game box scores.
No inferred ranks or fake player targets. Missing categories stay absent.
"""
import json, re, urllib.request, statistics
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event='
FIELDS=['pass_attempts_allowed','completions_allowed','passing_yards_allowed','passing_tds_allowed','rush_attempts_allowed','rushing_yards_allowed','rushing_tds_allowed','targets_allowed','receptions_allowed']
def number(v):
    try:return float(str(v).replace(',',''))
    except (TypeError,ValueError):return None
def parse_box(payload):
    """Return team keyed observed offensive stats from ESPN boxscore."""
    box=payload.get('boxscore') or {}
    out={}
    for side in box.get('players') or []:
        team=(side.get('team') or {}).get('displayName')
        if not team:continue
        values={'overall':{},'qb':{},'rb':{},'wr':{},'te':{}}
        for category in side.get('statistics') or []:
            name=str(category.get('name') or category.get('type') or '').lower()
            labels=[str(x).lower() for x in category.get('labels') or []]
            for athlete in category.get('athletes') or []:
                raw=athlete.get('stats') or []
                position=str(((athlete.get('athlete') or {}).get('position') or {}).get('abbreviation') or '').lower()
                buckets=[values['overall']] + ([values[position]] if position in ('qb','rb','wr','te') else [])
                for i,label in enumerate(labels):
                    if i>=len(raw):continue
                    value=raw[i]
                    if name=='passing':
                        if label in ('cmp/att','c/att') and '/' in str(value):
                            try:
                                cmp,att=map(int,str(value).split('/')[:2])
                                for bucket in buckets:
                                    bucket['completions_allowed']=bucket.get('completions_allowed',0)+cmp
                                    bucket['pass_attempts_allowed']=bucket.get('pass_attempts_allowed',0)+att
                            except ValueError:pass
                        if label in ('yds','yards'):
                            v=number(value)
                            if v is not None:
                                for bucket in buckets:bucket['passing_yards_allowed']=bucket.get('passing_yards_allowed',0)+v
                        if label in ('td','tds'):
                            v=number(value)
                            if v is not None:
                                for bucket in buckets:bucket['passing_tds_allowed']=bucket.get('passing_tds_allowed',0)+v
                    elif name=='rushing':
                        key={'car':'rush_attempts_allowed','att':'rush_attempts_allowed','yds':'rushing_yards_allowed','td':'rushing_tds_allowed'}.get(label)
                        v=number(value)
                        if key and v is not None:
                            for bucket in buckets:bucket[key]=bucket.get(key,0)+v
                    elif name=='receiving':
                        key={'rec':'receptions_allowed','tgt':'targets_allowed','tar':'targets_allowed'}.get(label)
                        v=number(value)
                        if key and v is not None:
                            for bucket in buckets:bucket[key]=bucket.get(key,0)+v
        out[team]=values
    return out
def season_of(dt):
    return dt.year-(1 if dt.month<2 else 0)
def build():
    completed=json.loads((ROOT/'feed/nfl_completed_games.json').read_text())['games']
    odds=json.loads((ROOT/'feed/americanfootball_nfl.json').read_text())['odds']
    upcoming={}
    for o in odds:
        if o.get('event_id') and o.get('event') and o.get('commence_time'):
            parts=o['event'].split(' @ ')
            if len(parts)==2:upcoming[o['event_id']]={'event_id':o['event_id'],'away':parts[0],'home':parts[1],'time':o['commence_time']}
    histories={};errors=[];calls=0
    for game in completed:
        date=datetime.fromisoformat(game['date'].replace('Z','+00:00'))
        if season_of(date) not in (2025,2026):continue
        eid=game.get('event_id')
        if not eid:continue
        try:
            req=urllib.request.Request(BASE+str(eid),headers={'User-Agent':'KennysSportsLab/1.0'})
            with urllib.request.urlopen(req,timeout=18) as response:payload=json.load(response)
            calls+=1
            offensive=parse_box(payload)
            for defense,offense in ((game['home'],game['away']),(game['away'],game['home'])):
                stats=offensive.get(offense)
                if stats:histories.setdefault(defense,[]).append((date,stats))
        except Exception as exc:
            errors.append({'event_id':eid,'reason':type(exc).__name__})
    events=[]
    for g in upcoming.values():
        kickoff=datetime.fromisoformat(g['time'].replace('Z','+00:00'))
        season=season_of(kickoff)
        matchup={}
        for period,year in (('season',season),('last4',season),('previous',season-1)):
            samples_by_side={}
            for side,team in (('home',g['home']),('away',g['away'])):
                samples=[(date,stats) for date,stats in histories.get(team,[]) if season_of(date)==year and date<kickoff]
                samples.sort(key=lambda x:x[0],reverse=True)
                if period=='last4':samples=samples[:4]
                samples_by_side[side]=samples
            matchup[period]={}
            for position in ('overall','qb','rb','wr','te'):
                sides={}
                for side,samples in samples_by_side.items():
                    agg={}
                    for field in FIELDS:
                        nums=[stats[position][field] for _,stats in samples if field in stats.get(position,{})]
                        if nums:agg[field]={'value':round(statistics.mean(nums),2),'sample_size':len(nums)}
                    if agg:agg['summary']=str(len(samples))+' observed '+str(year)+' games · '+position.upper()
                    sides[side]=agg
                matchup[period][position]=sides
        events.append({'event_id':g['event_id'],'matchup_stats':matchup})
    if not histories:raise SystemExit('No valid boxscore history fetched; refusing to replace existing snapshot')
    out={'source':'espn-public-nfl-summary-boxscore','generated_at':datetime.now(timezone.utc).isoformat(),'games_scanned':calls,'games_failed':len(errors),'teams_with_data':len(histories),'errors':errors[:20],'events':events}
    path=ROOT/'feed/americanfootball_nfl_defensive_comparison.json'
    path.write_text(json.dumps(out,separators=(',',':'))+chr(10))
    print('Saved',len(events),'event comparisons;',len(histories),'teams;',calls,'box scores;',len(errors),'failed')
if __name__=='__main__':build()
