import json,datetime,collections
d=json.load(open('feed/armchairlogan_history.json'))
names=dict(zip('ARI ATL BAL BUF CAR CHI CIN CLE DAL DEN DET GB HOU IND JAX KC LV LAC LA MIA MIN NE NO NYG NYJ PHI PIT SF SEA TB TEN WAS'.split(),'Arizona Cardinals|Atlanta Falcons|Baltimore Ravens|Buffalo Bills|Carolina Panthers|Chicago Bears|Cincinnati Bengals|Cleveland Browns|Dallas Cowboys|Denver Broncos|Detroit Lions|Green Bay Packers|Houston Texans|Indianapolis Colts|Jacksonville Jaguars|Kansas City Chiefs|Las Vegas Raiders|Los Angeles Chargers|Los Angeles Rams|Miami Dolphins|Minnesota Vikings|New England Patriots|New Orleans Saints|New York Giants|New York Jets|Philadelphia Eagles|Pittsburgh Steelers|San Francisco 49ers|Seattle Seahawks|Tampa Bay Buccaneers|Tennessee Titans|Washington Commanders'.split('|')))
def cipher(n):
 a=[ord(c)-64 for c in n.upper() if 'A'<=c<='Z']
 return {sum(a),sum((x-1)%9+1 for x in a),sum(27-x for x in a),sum((26-x)%9+1 for x in a)}
def targets(day):
 t=datetime.date.fromisoformat(day)
 return {t.day,t.month+t.day,sum(map(int,str(t.year)+str(t.month)+str(t.day))),t.timetuple().tm_yday,(datetime.date(t.year,12,31)-t).days}
stats=collections.defaultdict(lambda:dict(games=0,correct=0,home_baseline=0))
for day,a,b,x,y,kind in d['games']:
 if day<'2020-01-01' or a not in names or b not in names or x==y:continue
 # Modern franchise names are stable from 2020 except Washington renamed in 2022.
 if day<'2022-02-02' and 'WAS' in (a,b):continue
 if day<'2022-01-01' and 'LA' in (a,b):continue
 v=targets(day); aa=len(cipher(names[a])&v); bb=len(cipher(names[b])&v)
 if aa==bb:continue
 key='2020-2023 development' if day<'2024-01-01' else '2024 onward holdout'
 z=stats[key];z['games']+=1;z['correct']+=int((aa>bb)==(x>y));z['home_baseline']+=int(y>x)
out={'source':d['source'],'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rule':'Team-name calendar exact-match count only; ties abstain; excludes tied games. Retrospective holdout, not prospective validation.','results':dict(stats)}
json.dump(out,open('feed/gematria_backtest.json','w'),indent=2)
print(json.dumps(out))
