"""Independent free ESPN roster cross-check for archived NFL player props.

Roster listing is not proof of game-day active status, lineup, or market freshness.
Fail closed when source is unavailable or player identity is ambiguous.
"""
import json
import re
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

TEAMS={
"Arizona Cardinals":"ari","Atlanta Falcons":"atl","Baltimore Ravens":"bal",
"Buffalo Bills":"buf","Carolina Panthers":"car","Chicago Bears":"chi",
"Cincinnati Bengals":"cin","Cleveland Browns":"cle","Dallas Cowboys":"dal",
"Denver Broncos":"den","Detroit Lions":"det","Green Bay Packers":"gb",
"Houston Texans":"hou","Indianapolis Colts":"ind","Jacksonville Jaguars":"jax",
"Kansas City Chiefs":"kc","Las Vegas Raiders":"lv","Los Angeles Chargers":"lac",
"Los Angeles Rams":"lar","Miami Dolphins":"mia","Minnesota Vikings":"min",
"New England Patriots":"ne","New Orleans Saints":"no","New York Giants":"nyg",
"New York Jets":"nyj","Philadelphia Eagles":"phi","Pittsburgh Steelers":"pit",
"San Francisco 49ers":"sf","Seattle Seahawks":"sea","Tampa Bay Buccaneers":"tb",
"Tennessee Titans":"ten","Washington Commanders":"wsh"}
URL="https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team}/roster"

def normalize(value):
    return re.sub(r"[^a-z0-9]","",str(value).casefold())

def participants(event):
    parts=str(event).split(" @ ")
    if len(parts)!=2 or any(p not in TEAMS for p in parts):return ()
    return tuple(parts)

def roster_names(payload):
    names=set()
    def visit(node):
        if isinstance(node,dict):
            if isinstance(node.get("athlete"),dict):visit(node["athlete"])
            if isinstance(node.get("fullName"),str):names.add(normalize(node["fullName"]))
            if isinstance(node.get("displayName"),str):names.add(normalize(node["displayName"]))
            for key in ("athletes","items","groups","entries"):
                if isinstance(node.get(key),list):
                    for item in node[key]:visit(item)
        elif isinstance(node,list):
            for item in node:visit(item)
    visit(payload)
    return names

def fetch_roster(team):
    request=urllib.request.Request(URL.format(team=TEAMS[team]),headers={"User-Agent":"KennysSportsLab/1.0"})
    with urllib.request.urlopen(request,timeout=15) as response:
        data=response.read(2_000_001)
    if len(data)>2_000_000:raise ValueError("ESPN roster payload too large")
    return roster_names(json.loads(data))

def assess(props, rosters, unavailable=()):
    rows=props.get("odds",[])
    if not isinstance(rows,list):rows=[]
    counts={"quotes":len(rows),"roster_listed_quotes":0,"not_listed_quotes":0,
            "ambiguous_player_quotes":0,"unverifiable_quotes":0}
    findings=defaultdict(lambda:{"quotes":0,"status":"unverifiable","teams":[]})
    for row in rows:
        if not isinstance(row,dict):
            counts["unverifiable_quotes"]+=1
            continue
        name=row.get("player","")
        teams=participants(row.get("event"))
        key=str(name)
        entry=findings[key]
        entry["quotes"]+=1
        if not name or not teams or any(team in unavailable or team not in rosters for team in teams):
            counts["unverifiable_quotes"]+=1
            continue
        matches=[team for team in teams if normalize(name) in rosters[team]]
        if len(matches)==1:
            counts["roster_listed_quotes"]+=1
            entry["teams"]=sorted(set(entry["teams"]+[matches[0]]))
            entry["status"]="listed_on_espn_roster"
        elif len(matches)>1:
            counts["ambiguous_player_quotes"]+=1
            entry["status"]="ambiguous"
        else:
            counts["not_listed_quotes"]+=1
            entry["status"]="not_listed_on_either_roster"
    return {"status":"roster_research_only_not_bet_eligible","counts":counts,
            "roster_teams_fetched":sorted(rosters),
            "roster_teams_unavailable":sorted(unavailable),
            "players":dict(sorted(findings.items())),
            "current_roster_source_connected":bool(rosters),
            "lineup_verified":False,"injury_status_verified":False,
            "market_fresh":False,"verified_betting_recommendations":0,
            "note":"ESPN roster listings are independent roster evidence only. Not game-day active lists, injury confirmations, validated projections or live betting odds."}

def main():
    props_path=Path("feed/nfl_props.json")
    props=json.loads(props_path.read_text()) if props_path.exists() else {}
    teams=set()
    for row in props.get("odds",[]):
        if isinstance(row,dict):teams.update(participants(row.get("event")))
    rosters={};unavailable=[]
    for team in sorted(teams):
        try:
            names=fetch_roster(team)
            if not names:raise ValueError("Empty roster")
            rosters[team]=names
        except (OSError,ValueError,TimeoutError,KeyError) as exc:
            unavailable.append(team)
            print("Roster unavailable:",team,type(exc).__name__)
    result=assess(props,rosters,unavailable)
    result["generated_at"]=datetime.now(timezone.utc).isoformat()
    result["source"]="ESPN public NFL team roster endpoint"
    path=Path("feed/nfl_roster_crosscheck.json")
    path.write_text(json.dumps(result,indent=2)+"\n")
    print("NFL roster audit:",result["counts"],"fetched teams:",len(rosters))

if __name__=="__main__":
    main()
