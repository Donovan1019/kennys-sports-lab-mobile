import json, urllib.request, datetime, concurrent.futures
BASE='https://site.api.espn.com/apis/site/v2/sports/football/nfl'
CORE='https://sports.core.api.espn.com/v2/sports/football/leagues/nfl'
now=datetime.datetime.now(datetime.timezone.utc)
season=now.year if now.month>=7 else now.year-1
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url.replace('http://','https://'),headers={'User-Agent':'Mozilla/5.0'}),timeout=12) as r: return json.load(r)
def resolve(x):
    return get(x['$ref']) if '$ref' in x and len(x)==1 else x
def items(url):
    d=get(url+'?limit=100')
    rows=d['items']
    for p in range(2,d.get('pageCount',1)+1): rows+=get(url+'?limit=100&page='+str(p))['items']
    return rows
def player(a):
    a=resolve(a)
    if not (a.get('displayName') or a.get('fullName')) and a.get('$ref'): a=get(a['$ref'])
    return a
def team(t):
    tid=str(t['id']); out={'team':t['displayName'],'id':tid}
    try:
        rows=[]
        for ref in items(CORE+'/teams/'+tid+'/injuries'):
            x=resolve(ref)
            date=x.get('date','')
            if not date or datetime.datetime.fromisoformat(date.replace('Z','+00:00'))<now-datetime.timedelta(days=30): continue
            a=player(x['athlete']); name=a.get('displayName') or a.get('fullName')
            if not name or not x.get('status'): raise ValueError('Incomplete injury record')
            rows.append({'name':name,'status':x['status'],'date':date,'position':a.get('position',{}).get('abbreviation')})
        out['injuries']={'status':'reported','data':rows}
    except Exception as e: out['injuries']={'status':'unavailable','reason':str(e)}
    try:
        starters=[]
        for chart in items(CORE+'/seasons/'+str(season)+'/teams/'+tid+'/depthcharts'):
            chart=resolve(chart)
            for key,p in chart.get('positions',{}).items():
                for a in p.get('athletes',[]):
                    if str(a.get('rank'))!='1': continue
                    q=player(a['athlete']); name=q.get('displayName') or q.get('fullName')
                    if name: starters.append({'position':p.get('position',{}).get('abbreviation',key.upper()),'name':name})
        if not any(x['position']=='QB' for x in starters): raise ValueError('Missing QB1')
        out['depthcharts']={'status':'reported','data':starters}
    except Exception as e: out['depthcharts']={'status':'unavailable','reason':str(e)}
    return out
teams=[x['team'] for x in get(BASE+'/teams')['sports'][0]['leagues'][0]['teams']]
assert len(teams)==32
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool: rows=list(pool.map(team,teams))
coverage={k:sum(t[k]['status']=='reported' for t in rows) for k in ('injuries','depthcharts')}
print('Coverage:',coverage)
for t in rows:
    for k in coverage:
        if t[k]['status']!='reported': print(t['team'],k,t[k]['reason'])
json.dump({'fetched_at':now.isoformat(),'source':'ESPN NFL Core API','coverage':coverage,'teams':rows},open('feed/armchairlogan_availability.json','w'),indent=2)
assert all(coverage.values()),'Zero coverage: availability incomplete'
