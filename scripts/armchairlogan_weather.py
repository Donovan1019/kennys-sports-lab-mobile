import json, datetime, urllib.request, urllib.parse, concurrent.futures
UTC=datetime.timezone.utc
now=datetime.datetime.now(UTC)
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'KennySportsLab weather collector'}),timeout=25) as r: return json.load(r)
def dt(s): return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
games=json.load(open('feed/armchairlogan_state.json'))['games']
upcoming=[g for g in games if g.get('kickoff') and now<=dt(g['kickoff'])<=now+datetime.timedelta(days=7)]
dates=now.strftime('%Y%m%d')+'-'+(now+datetime.timedelta(days=7)).strftime('%Y%m%d')
events_by_id={}
for day in range(8):
    date=(now+datetime.timedelta(days=day)).strftime('%Y%m%d')
    for event in get('https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates='+date)['events']:
        events_by_id[event['id']]=event
events=list(events_by_id.values())
def collect(e):
    c=e['competitions'][0]; v=c['venue']; kickoff=dt(c['date']); name=v['fullName']
    row={'event_id':e['id'],'kickoff':c['date'],'stadium':name,'venue_id':v.get('id'),'teams':{x['homeAway']:x['team']['abbreviation'] for x in c['competitors']},'status':'unavailable','roof_status':'unconfirmed'}
    try:
        detail=get('https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event='+e['id'])
        venue=detail.get('gameInfo',{}).get('venue',v)
        loc=venue.get('address',{}); coord=venue.get('coordinates') or v.get('coordinates')
        if not coord:
            # Geocode the named venue, never substitute a city centroid.
            q=urllib.parse.urlencode({'q':name+', '+loc.get('city','')+', '+loc.get('state',''),'format':'jsonv2','limit':3})
            matches=get('https://nominatim.openstreetmap.org/search?'+q)
            match=next((m for m in matches if m.get('type') in ('stadium','sports_centre') and name.lower() in m.get('display_name','').lower()),None)
            if not match: raise ValueError('Exact stadium coordinates unavailable')
            coord={'latitude':float(match['lat']),'longitude':float(match['lon'])}
        lat=float(coord['latitude']); lon=float(coord['longitude'])
        row.update(latitude=lat,longitude=lon,indoor_designation=venue.get('indoor',v.get('indoor')))
        fields='temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,wind_speed_10m,wind_gusts_10m,wind_direction_10m,weather_code'
        query=urllib.parse.urlencode({'latitude':lat,'longitude':lon,'hourly':fields,'temperature_unit':'fahrenheit','wind_speed_unit':'mph','precipitation_unit':'inch','timezone':'UTC','forecast_days':8})
        d=get('https://api.open-meteo.com/v1/forecast?'+query); h=d['hourly']
        rows=[{'time_utc':t+'Z',**{k:h[k][i] for k in fields.split(',')}} for i,t in enumerate(h['time']) if kickoff-datetime.timedelta(hours=1)<=dt(t+'Z')<=kickoff+datetime.timedelta(hours=4)]
        if not rows: raise ValueError('No kickoff forecast')
        row.update(status='reported',hourly=rows,source='Open-Meteo',units=d['hourly_units'])
    except Exception as exc: row['reason']=str(exc)
    return row
# Sequential venue lookup respects public geocoder usage limits.
import time
rows=[]
for e in events:
    if now<=dt(e['date'])<=now+datetime.timedelta(days=7):
        rows.append(collect(e)); time.sleep(1.1)
json.dump({'fetched_at':now.isoformat(),'games':rows,'coverage':sum(r['status']=='reported' for r in rows),'expected':len(upcoming)},open('feed/armchairlogan_weather.json','w'),indent=2)
print('Weather coverage:',sum(r['status']=='reported' for r in rows),'/',len(rows),'scheduled events')
