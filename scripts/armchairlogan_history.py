import csv,json,urllib.request,datetime
url='https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv'
now=datetime.datetime.now(datetime.timezone.utc)
with urllib.request.urlopen(url,timeout=60) as f: rows=list(csv.DictReader(f.read().decode('utf-8-sig').splitlines()))
games=[]; seen=set(); coaches=[]
aliases={'OAK':'LV','SD':'LAC','STL':'LA','LAR':'LA','WSH':'WAS'}
for x in rows:
    if x['game_id'] in seen or not x['away_score'] or not x['home_score'] or x['gameday']>=now.date().isoformat():continue
    if x['game_type'] not in ('REG','WC','DIV','CON','SB'):continue
    seen.add(x['game_id'])
    games.append([x['gameday'],aliases.get(x['away_team'],x['away_team']),aliases.get(x['home_team'],x['home_team']),int(float(x['away_score'])),int(float(x['home_score'])),x['game_type']])
    if x.get('away_coach') and x.get('home_coach'):
        coaches.append([x['gameday'],aliases.get(x['away_team'],x['away_team']),aliases.get(x['home_team'],x['home_team']),x['away_coach'],x['home_coach'],int(float(x['away_score'])),int(float(x['home_score']))])
assert len(games)>6000
games.sort(reverse=True)
with open('feed/armchairlogan_history.json','w') as f:json.dump({'source':url,'fetched_at':now.isoformat(),'start':min(x[0] for x in games),'games':games,'coaches':sorted(coaches,reverse=True)},f,separators=(',',':'))
print('Historical games:',len(games))
