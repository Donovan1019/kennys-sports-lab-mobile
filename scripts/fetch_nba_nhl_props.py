"""Opt-in, credit-capped NBA/NHL player-prop collector. No scheduled paid calls."""
import json,os,sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode,quote
from urllib.request import Request,urlopen

MARKETS={
 'nba':('basketball_nba',('player_points','player_rebounds','player_assists','player_threes','player_blocks','player_steals','player_points_rebounds_assists')),
 'nhl':('icehockey_nhl',('player_points','player_goals','player_assists','player_shots_on_goal','player_saves')),
}
BOOKS=('draftkings','fanduel')
def get(url):
 with urlopen(Request(url,headers={'User-Agent':'KennysSportsLab/1.0'}),timeout=40) as response:
  return json.load(response),response.headers.get('x-requests-remaining')
def collect(sport,limit,key):
 sport_key,markets=MARKETS[sport];base='https://api.the-odds-api.com/v4/sports/'+sport_key
 events,_=get(base+'/events?'+urlencode({'apiKey':key}))
 if not isinstance(events,list):raise ValueError('Invalid event list')
 now=datetime.now(timezone.utc)
 events=sorted((e for e in events if e.get('id') and e.get('home_team') and e.get('away_team') and e.get('commence_time') and datetime.fromisoformat(e['commence_time'].replace('Z','+00:00'))>now),key=lambda e:e['commence_time'])[:limit]
 rows=[];errors=[]
 for event in events:
  try:
   data,remaining=get(base+'/events/'+quote(event['id'],safe='')+'/odds?'+urlencode({'apiKey':key,'bookmakers':','.join(BOOKS),'markets':','.join(markets),'oddsFormat':'american'}))
   for book in data.get('bookmakers',[]):
    if book.get('key') not in BOOKS:continue
    for market in book.get('markets',[]):
     if market.get('key') not in markets:continue
     for outcome in market.get('outcomes',[]):
      price=outcome.get('price');point=outcome.get('point')
      if not outcome.get('description') or not isinstance(price,(int,float)) or not isinstance(point,(int,float)):continue
      if -100<price<100:continue
      rows.append({'event_id':event['id'],'event':event['away_team']+' @ '+event['home_team'],'commence_time':event['commence_time'],'market':market['key'],'player':outcome['description'],'selection':outcome.get('name'),'point':point,'price':price,'bookmaker':book['key'],'updated_at':market.get('last_update') or book.get('last_update')})
   print(sport,event['id'],'quotes',len(rows),'remaining credits',remaining)
  except Exception as exc:
   errors.append({'event_id':event['id'],'error':type(exc).__name__});print(sport,'event unavailable',type(exc).__name__)
 if not rows:raise ValueError('No valid player props; prior feed preserved')
 out={'sport':sport_key,'source':'the-odds-api-v4-event-props','fetched_at':now.isoformat(),'markets_requested':list(markets),'events_requested':len(events),'books':list(BOOKS),'errors':errors,'odds':rows}
 path=Path('feed/'+sport+'_props.json');path.parent.mkdir(exist_ok=True)
 path.write_text(json.dumps(out,separators=(',',':'))+'\n')
 print('Saved',len(rows),'quotes to',path)
def main():
 sport=os.getenv('SPORT','');key=os.getenv('THE_ODDS_API_KEY','')
 try:limit=int(os.getenv('MAX_EVENTS','0'))
 except ValueError:limit=0
 if sport not in MARKETS or not 1<=limit<=3 or not key:
  print('Explicit SPORT=nba|nhl, MAX_EVENTS=1..3 and API secret required; no calls made');return 2
 try:collect(sport,limit,key);return 0
 except Exception as exc:print('Collection failed:',type(exc).__name__,str(exc));return 1
if __name__=='__main__':sys.exit(main())
