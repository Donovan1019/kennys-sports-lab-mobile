"""Refresh recent verified NBA/NHL final scores from free ESPN daily scoreboards.

Only dates within the recent window are fetched. Preserve historical rows and
fail without writing if any required daily request fails.
"""
import json
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.request import Request,urlopen
from scripts.connect_nba_nhl_scores import parse_league
from scripts.connect_nfl_team_scores import parse_scoreboard

LEAGUES={"nba":"basketball","nhl":"hockey","nfl":"football"}

def merge(existing,incoming):
    by_key={}
    for g in existing+incoming:
        if not isinstance(g,dict):continue
        try:
            key=(g["date"],g["away"],g["home"])
            if not all(key):continue
            if type(g["away_score"]) not in (int,float) or type(g["home_score"]) not in (int,float):continue
            by_key[key]=g
        except (KeyError,TypeError):continue
    return sorted(by_key.values(),key=lambda g:g["date"])

def refresh(league,now,days=8):
    if league not in LEAGUES:raise ValueError("Unsupported league")
    if now.tzinfo is None:raise ValueError("Timezone-aware clock required")
    path=Path(f"feed/{league}_completed_games.json")
    old=json.loads(path.read_text()) if path.exists() else {"games":[]}
    incoming=[]
    successful_days=0
    failures=[]
    for offset in range(days):
        day=(now.date()-timedelta(days=offset)).strftime("%Y%m%d")
        url=f"https://site.api.espn.com/apis/site/v2/sports/{LEAGUES[league]}/{league}/scoreboard?dates={day}"
        req=Request(url,headers={"User-Agent":"KennysSportsLab/1.0","Accept":"application/json"})
        try:
            with urlopen(req,timeout=25) as response:
                payload=json.load(response)
            if not isinstance(payload,dict) or not isinstance(payload.get("events"),list):
                raise ValueError("malformed ESPN scoreboard")
            parsed=parse_scoreboard(payload) if league=="nfl" else parse_league(payload)
        except (OSError,ValueError,TypeError,KeyError) as exc:
            failures.append(f"{day}: {type(exc).__name__}: {exc}")
            continue
        successful_days+=1
        incoming.extend(parsed)
    if failures:
        print(f"{league}: {len(failures)} scoreboard fetch failures; preserved existing verified rows; " + "; ".join(failures))
    if successful_days==0:
        if old.get("games"):
            print(f"{league}: no fresh scoreboard responses; retaining cached verified games")
            return 0,len(old["games"])
        raise ValueError(f"{league}: no valid scoreboard responses and no cached results")
    merged=merge(old.get("games",[]),incoming)
    if not merged:
        if league=="nfl" and not incoming and not old.get("games"):
            return 0,0
        raise ValueError(f"{league}: no verified games; refusing empty overwrite")
    result={"source":"espn-public-completed-league-games","league":league,"fetched_at":now.isoformat(),"games":merged}
    path.write_text(json.dumps(result,indent=2)+"\n")
    return len(incoming),len(merged)

def main():
    now=datetime.now(timezone.utc)
    for league in LEAGUES:
        new,total=refresh(league,now)
        print(f"{league}: {new} recent verified completed-game records; {total} historical records retained")
if __name__=="__main__":main()
