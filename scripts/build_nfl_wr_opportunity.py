#!/usr/bin/env python3
"""Build verified NFL WR opportunity data from a supplied nflverse-style weekly CSV.
Usage: python scripts/build_nfl_wr_opportunity.py --input weekly.csv --season 2026
No estimated routes, first reads or end-zone targets are invented.
"""
import argparse,csv,json,math,pathlib,datetime,collections
def number(row,*keys):
    for k in keys:
        v=row.get(k)
        if v is not None and str(v).strip() not in ('','NA','NaN','nan','null'):
            try:
                n=float(v)
                if math.isfinite(n) and n>=0:return n
            except (ValueError,TypeError):pass
    return None
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True,help='Verified weekly player CSV')
    p.add_argument('--season',type=int,required=True)
    p.add_argument('--output',default='feed/nfl_wr_opportunity.json')
    a=p.parse_args()
    with open(a.input,newline='',encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    mandatory={'player_id','player_name','recent_team','position','season','week','targets'}
    if not rows or not mandatory.issubset(rows[0]):
        raise SystemExit('Missing required weekly player columns: '+','.join(sorted(mandatory-set(rows[0] if rows else []))))
    # Require complete receiving-position coverage before deriving a team denominator.
    # The denominator includes all recorded targets, not just WR targets.
    buckets=collections.defaultdict(list)
    valid=[]
    for row in rows:
        if str(row.get('season'))!=str(a.season) or str(row.get('season_type','REG')).upper() not in ('REG','2'):continue
        if not row.get('player_id') or not row.get('recent_team') or number(row,'targets') is None:continue
        week=number(row,'week')
        if week is None:continue
        key=(row['recent_team'],int(week))
        buckets[key].append(row)
        valid.append((key,row))
    games=[]
    for (team,week),players in sorted(buckets.items()):
        # Reject partial team records; no denominator if team has no QB or too few
        # receiving contributors. This is a conservative integrity check, not proof
        # of complete coverage.
        positions={r['position'] for r in players}
        if len({r['player_id'] for r in players})<5:continue
        total=sum(number(r,'targets') or 0 for r in players)
        # A complete, independently supplied team target total is preferred.
        # Otherwise the sum of individual player rows is not sufficient proof
        # of full team coverage: do not publish a misleading share.
        declared={number(r,'team_targets') for r in players if number(r,'team_targets') is not None}
        verified_total=next(iter(declared)) if len(declared)==1 else None
        denominator_source='explicit_team_targets' if verified_total is not None else None
        # nflverse weekly player data has no team_targets column. Use all
        # recorded player targets only when consistent with team QB attempts.
        if verified_total is None and not declared:
            qb_attempts=sum(number(r,'attempts','passing_attempts') or 0 for r in players if r.get('position')=='QB')
            if qb_attempts >= total and qb_attempts-total <= max(12,qb_attempts*0.25):
                verified_total=total
                denominator_source='player_targets_qb_attempts_consistency_check'
        if len(declared)>1:continue
        if verified_total is not None and abs(total-verified_total)>0.01:continue
        if total<=0:continue
        for row in players:
            if row['position'] not in ('WR','RB','TE'):continue
            def metric(*keys):return number(row,*keys)
            item={'player_id':row['player_id'],'player_name':row['player_name'],
                  'position':row['position'],'team':team,'season':a.season,'denominator_source':denominator_source,'game_id':f'{a.season}-{week}-{team}',
                  'game_date':row.get('game_date') or None,'week':week,
                  'targets':metric('targets'),'team_targets':verified_total,
                  'receptions':metric('receptions'),'receiving_yards':metric('receiving_yards'),
                  'receiving_tds':metric('receiving_tds','receiving_touchdowns'),
                  'routes_run':metric('routes_run'),
                  'team_dropbacks':metric('team_dropbacks'),
                  'first_read_targets':metric('first_read_targets'),
                  'team_first_read_targets':metric('team_first_read_targets'),
                  'end_zone_targets':metric('end_zone_targets'),
                  'team_end_zone_targets':metric('team_end_zone_targets'),
                  'offensive_snaps':metric('offensive_snaps')}
            # Never mix nullable charted metrics with basic stats unless the
            # source explicitly supplied them in the input.
            games.append(item)
    if not games:raise SystemExit('No validated team-week opportunity rows; refusing to publish empty feed')
    payload={'season':a.season,'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'source':'supplied verified weekly CSV; charted fields only when present',
             'coverage':'team-weeks with >=5 recorded players; target denominators checked against QB passing attempts or explicit team totals',
             'games':games}
    out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,separators=(',',':'))+'\n')
    print(f'Published {len(games)} player-week rows to {out}')
if __name__=='__main__':main()
