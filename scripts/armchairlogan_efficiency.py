import json, urllib.request, datetime, csv, gzip, io
from collections import defaultdict
now=datetime.datetime.now(datetime.timezone.utc)
season=now.year if now.month>=8 else now.year-1
url=f'https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.csv.gz'
with urllib.request.urlopen(url,timeout=120) as response:
    raw=response.read()
rows=csv.DictReader(io.TextIOWrapper(gzip.GzipFile(fileobj=io.BytesIO(raw)),encoding='utf-8'))
stats=defaultdict(lambda: {'off':[],'def':[]})
for p in rows:
    if p.get('season_type')!='REG' or p.get('play_type') not in ('pass','run') or not p.get('posteam') or not p.get('defteam'): continue
    try:
        date=datetime.date.fromisoformat(p['game_date'])
        if date>=now.date(): continue
        epa=float(p['epa']); yards=float(p['yards_gained']); field=float(p['yardline_100'])
        if not all(map(__import__('math').isfinite,(epa,yards,field))): continue
    except (ValueError,KeyError,TypeError): continue
    item=(epa,yards,field,p['play_type'],p.get('qb_hit')=='1',p.get('sack')=='1')
    stats[p['posteam']]['off'].append(item)
    stats[p['defteam']]['def'].append(item)
def summarize(a):
    n=len(a)
    if not n:return None
    passes=[x for x in a if x[3]=='pass']; red=[x for x in a if x[2]<=20]
    return {'plays':n,'epa_per_play':sum(x[0] for x in a)/n,'success_rate':sum(x[0]>0 for x in a)/n,'explosive_rate':sum(x[1]>=(20 if x[3]=='pass' else 10) for x in a)/n,'red_zone_epa':sum(x[0] for x in red)/len(red) if red else None,'qb_hit_or_sack_rate':sum(x[4] or x[5] for x in passes)/len(passes) if passes else None}
assert len(stats)==32 and all(len(v['off'])>=100 and len(v['def'])>=100 for v in stats.values()), 'Incomplete season coverage'
out={'source':url,'fetched_at':now.isoformat(),'season':season,'teams':{k:{side:summarize(a) for side,a in v.items()} for k,v in stats.items()}}
with open('feed/armchairlogan_efficiency.json','w') as f:json.dump(out,f,indent=2,allow_nan=False)
print('Efficiency coverage:',len(stats))
