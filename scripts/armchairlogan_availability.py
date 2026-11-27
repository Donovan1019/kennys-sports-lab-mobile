import json, urllib.request, datetime, concurrent.futures
BASE='https://site.api.espn.com/apis/site/v2/sports/football/nfl'
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=20) as r: return json.load(r)
def team(t):
    out={'team':t['displayName'],'id':t['id']}
    for key in ('injuries','depthcharts'):
        try:
            d=get(BASE+'/teams/'+t['id']+'/'+key)
            rows=d.get(key)
            if not isinstance(rows,list): raise ValueError('Unexpected source schema')
            out[key]={'status':'reported','data':rows}
        except Exception as e: out[key]={'status':'unavailable','reason':str(e)}
    return out
teams=[x['team'] for x in get(BASE+'/teams')['sports'][0]['leagues'][0]['teams']]
assert len(teams)==32
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool: rows=list(pool.map(team,teams))
out={'fetched_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'ESPN NFL team reports','teams':rows}
json.dump(out,open('feed/armchairlogan_availability.json','w'),indent=2)
print('Coverage:',{k:sum(t[k]['status']=='reported' for t in rows) for k in ('injuries','depthcharts')})
