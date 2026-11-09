#!/usr/bin/env python3
"""Conservative cross-source NFL injury/usage research join; never a verified identity or inactive flag."""
import json,re
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
TEAMS={"Arizona Cardinals":"ARI","Atlanta Falcons":"ATL","Baltimore Ravens":"BAL","Buffalo Bills":"BUF","Carolina Panthers":"CAR","Chicago Bears":"CHI","Cincinnati Bengals":"CIN","Cleveland Browns":"CLE","Dallas Cowboys":"DAL","Denver Broncos":"DEN","Detroit Lions":"DET","Green Bay Packers":"GB","Houston Texans":"HOU","Indianapolis Colts":"IND","Jacksonville Jaguars":"JAX","Kansas City Chiefs":"KC","Las Vegas Raiders":"LV","Los Angeles Chargers":"LAC","Los Angeles Rams":"LA","Miami Dolphins":"MIA","Minnesota Vikings":"MIN","New England Patriots":"NE","New Orleans Saints":"NO","New York Giants":"NYG","New York Jets":"NYJ","Philadelphia Eagles":"PHI","Pittsburgh Steelers":"PIT","San Francisco 49ers":"SF","Seattle Seahawks":"SEA","Tampa Bay Buccaneers":"TB","Tennessee Titans":"TEN","Washington Commanders":"WAS"}
ALIASES={"LAR":"LA","WSH":"WAS","JAC":"JAX","GBP":"GB"}
def norm(x):return re.sub(r"[^a-z0-9]","",str(x or "").lower())
def stamp(x):
 try:
  d=datetime.fromisoformat(str(x).replace("Z","+00:00"))
  return d if d.tzinfo else None
 except (ValueError,TypeError):return None
def join(usage,injury):
 checked=stamp(injury.get("checked_at"));now=datetime.now(timezone.utc)
 fresh=bool(checked and 0<=(now-checked).total_seconds()<=6*3600)
 index=defaultdict(list)
 for r in injury.get("injuries",[]):
  team=TEAMS.get(r.get("team"));name=norm(r.get("player"));t=stamp(r.get("reported_at"))
  if team and name and t:index[(team,name)].append(r)
 out={"generated_at":now.isoformat(),"status":"RESEARCH_ONLY","identity_verified":False,"game_day_status_verified":False,"injury_feed_fresh":fresh,"betting_eligible":False,"profiles_checked":0,"name_team_candidates":0,"historical_name_team_candidates":0,"ambiguous":0,"stale_or_missing":0,"no_match":0,"candidates":[]}
 for p in usage.get("profiles",[]):
  out["profiles_checked"]+=1
  team=ALIASES.get(str(p.get("team") or "").upper(),str(p.get("team") or "").upper())
  found=index.get((team,norm(p.get("name"))),[])
  if not found:out["no_match"]+=1;continue
  # Multiple distinct source statuses/timestamps must never silently overwrite one another.
  statuses={str(r.get("status") or "").strip().lower() for r in found}
  if len(statuses)>1:out["ambiguous"]+=1;continue
  latest=max(found,key=lambda r:stamp(r["reported_at"]))
  age=(now-stamp(latest["reported_at"])).total_seconds()
  if not fresh or age<0 or age>6*3600:\n   out["stale_or_missing"]+=1\n   out["historical_name_team_candidates"]+=1\n   continue
  out["name_team_candidates"]+=1
  out["candidates"].append({"player":p.get("name"),"nflverse_player_id":p.get("nflverse_player_id"),"espn_athlete_id":None,"team":team,"position":p.get("position"),"source_status":latest.get("status"),"reported_at":latest.get("reported_at"),"match_method":"NORMALIZED_NAME_AND_TEAM_ONLY","identity_verified":False,"game_day_active_verified":False,"game_day_inactive_verified":False,"projection_adjustment_eligible":False})
 return out
def main():
 root=Path(__file__).resolve().parent.parent
 usage=json.loads((root/"feed/nfl_usage_research.json").read_text())
 injury=json.loads((root/"feed/nfl_injury_observations.json").read_text())
 result=join(usage,injury)
 (root/"feed/nfl_injury_usage_crosscheck.json").write_text(json.dumps(result,indent=2)+"\n")
 print("NFL injury usage crosscheck",json.dumps({k:v for k,v in result.items() if k not in ("candidates","generated_at")}))
if __name__=="__main__":main()
