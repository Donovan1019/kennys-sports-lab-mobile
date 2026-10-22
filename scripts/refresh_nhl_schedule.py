"""Refresh NHL upcoming matchups from ESPN public scoreboard; no odds or roster claims."""
import json
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.request import Request,urlopen

def main():
 now=datetime.now(timezone.utc); games={}
 for offset in range(8):
  date=(now+timedelta(days=offset)).strftime('%Y%m%d')
  url=f'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates={date}'
  try:
   with urlopen(Request(url,headers={'User-Agent':'KSL research (public schedules)'}),timeout=15) as response:data=json.load(response)
  except Exception as exc:
   print(date,type(exc).__name__);continue
  for event in data.get('events',[]):
   competitions=event.get('competitions') or []
   if not competitions:continue
   teams=competitions[0].get('competitors',[])
   home=next((x.get('team',{}).get('displayName') for x in teams if x.get('homeAway')=='home'),None)
   away=next((x.get('team',{}).get('displayName') for x in teams if x.get('homeAway')=='away'),None)
   kickoff=event.get('date')
   if not home or not away or not kickoff:continue
   try:future=datetime.fromisoformat(kickoff.replace('Z','+00:00'))>now
   except ValueError:continue
   if not future:continue
   games[str(event.get('id'))]={'event_id':'espn-'+str(event.get('id')),'event':f'{away} @ {home}','home':home,'away':away,'commence_time':kickoff,'source':'ESPN scoreboard','teams':[]}
 if not games:raise SystemExit('No upcoming NHL events fetched; retaining prior feed')
 payload={'source':'ESPN public NHL scoreboard','source_detail':'Upcoming fixtures only. Player roster, lineup and sportsbook quotes not verified.','fetched_at':now.isoformat(),'games':sorted(games.values(),key=lambda x:x['commence_time'])}
 Path('feed/nhl_independent_game_inputs.json').write_text(json.dumps(payload,indent=2)+'\n')
 print('Saved',len(games),'upcoming NHL games')
if __name__=='__main__':main()
