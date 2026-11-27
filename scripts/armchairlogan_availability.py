import json, urllib.request, datetime, concurrent.futures
BASE='https://site.api.espn.com/apis/site/v2/sports/football/nfl'
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=20) as r: return json.load(r)
teams=[x['team'] for x in get(BASE+'/teams')['sports'][0]['leagues'][0]['teams']]
assert len(teams)==32
groups=get(BASE+'/injuries')['injuries']
assert isinstance(groups,list)
byid={str(g['team']['id']):g['injuries'] for g in groups if isinstance(g.get('injuries'),list)}
def team(t):
    tid=str(t['id']); out={'team':t['displayName'],'id':tid}
    rows=byid.get(tid)
    if rows is not None and all(x.get('athlete',{}).get('displayName') or x.get('athlete',{}).get('fullName') for x in rows):
        out['injuries']={'status':'reported','data':[{'name':x['athlete'].get('displayName') or x['athlete'].get('fullName'),'position':x['athlete'].get('position',{}).get('abbreviation'),'status':x.get('status'),'date':x.get('date')} for x in rows]}
    else: out['injuries']={'status':'unavailable','reason':'No validated team injury group'}
    try:
        d=get(BASE+'/teams/'+tid+'/depthcharts')
        charts=d.get('depthCharts',d.get('depthcharts'))
        if not isinstance(charts,list): raise ValueError('Unexpected keys: '+str(list(d)))
        starters=[]
        for chart in charts:
            for key,p in chart.get('positions',{}).items():
                for a in p.get('athletes',[]):
                    player=a.get('athlete',{})
                    name=player.get('displayName') or player.get('fullName')
                    if str(a.get('rank'))=='1' and name: starters.append({'position':p.get('position',{}).get('abbreviation',key),'name':name})
        if not any(x['position']=='QB' for x in starters): raise ValueError('Missing QB1')
        out['depthcharts']={'status':'reported','data':starters}
    except Exception as e: out['depthcharts']={'status':'unavailable','reason':str(e)}
    return out
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool: rows=list(pool.map(team,teams))
coverage={k:sum(t[k]['status']=='reported' for t in rows) for k in ('injuries','depthcharts')}
print('Coverage:',coverage)
assert all(coverage.values()),'Zero coverage: refusing publication'
json.dump({'fetched_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'ESPN NFL team reports','coverage':coverage,'teams':rows},open('feed/armchairlogan_availability.json','w'),indent=2)
