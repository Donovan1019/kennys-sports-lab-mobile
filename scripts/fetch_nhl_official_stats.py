#!/usr/bin/env python3
"""Manual NHL official game boxscore ingestion. Does not use ESPN zero SOG fields."""
import json, os, sys, urllib.request
from pathlib import Path
from datetime import date, datetime, timedelta, timezone

BASE="https://api-web.nhle.com/v1"
def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"KennysSportsLab/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=25) as response:
        data=response.read(6000000)
    return json.loads(data)
def integer(value):
    if isinstance(value,bool):return None
    try:
        x=float(value)
        return int(x) if x>=0 and x.is_integer() else None
    except (ValueError,TypeError):return None
def parse_boxscore(payload,game_id,game_date):
    if not isinstance(payload,dict):raise ValueError("Invalid NHL boxscore")
    rows=[]
    for side in ("awayTeam","homeTeam"):
        team=payload.get(side) or {}
        team_code=team.get("abbrev") or ""
        if isinstance(team_code,dict):team_code=team_code.get("default","")
        if not isinstance(team_code,str):team_code=""
        grouped=(payload.get("playerByGameStats") or {}).get("awayTeam" if side=="awayTeam" else "homeTeam") or {}
        for position in ("forwards","defense","goalies"):
            for player in grouped.get(position) or []:
                pid=player.get("playerId")
                name=player.get("name") or {}
                if isinstance(name,dict):name=(name.get("default") or "")
                if not name:name=((player.get("firstName") or {}).get("default","")+" "+(player.get("lastName") or {}).get("default","")).strip()
                if not pid or not name:continue
                vals={}
                for source,target in (("goals","Goals"),("assists","Assists"),("sog","Shots on goal"),("saves","Saves")):
                    v=integer(player.get(source))
                    if v is not None:vals[target]=v
                if "Goals" in vals and "Assists" in vals:vals["Points"]=vals["Goals"]+vals["Assists"]
                if not vals:continue
                rows.append({"id":str(pid),"name":name,"team":team_code,"game_id":str(game_id),"date":game_date,"values":vals,"home_away":"home" if side=="homeTeam" else "away","position_group":position})
    return rows
def main():
    days=int(os.environ.get("LOOKBACK_DAYS","14"))
    if not 1<=days<=31:raise ValueError("Lookback must be 1-31")
    path=Path("feed/nhl_official_player_stats.json")
    prior={}
    if path.exists():
        previous=json.loads(path.read_text())
        if previous.get("source")=="nhl-official-boxscore":
            for p in previous.get("players",[]):
                for g in p.get("games",[]):
                    prior[(p["id"],g["game_id"])]={"id":p["id"],"name":p["name"],"team":p["team"],**g}
    parsed=0;checked=0;errors=[]
    for offset in range(days):
        day=date.today()-timedelta(days=offset)
        try:
            schedule=fetch(f"{BASE}/score/{day.isoformat()}")
            games=schedule.get("games") or []
        except Exception as exc:
            errors.append({"date":day.isoformat(),"error":str(exc)[:180]});continue
        for game in games:
            gid=game.get("id")
            state=game.get("gameState")
            if not gid or state not in ("FINAL","OFF"):continue
            checked+=1
            try:
                box=fetch(f"{BASE}/gamecenter/{gid}/boxscore")
                rows=parse_boxscore(box,gid,day.isoformat())
                if not rows:raise ValueError("No valid player stats")
                for row in rows:prior[(row["id"],row["game_id"])]=row
                parsed+=1
            except Exception as exc:errors.append({"game_id":gid,"error":str(exc)[:180]})
    if not prior:raise SystemExit(f"No NHL official records: checked={checked}, parsed={parsed}, errors={errors[:5]}")
    players={}
    for row in prior.values():
        pid=row["id"]
        p=players.setdefault(pid,{"id":pid,"name":row["name"],"team":row["team"],"games":[]})
        p["name"]=row["name"];p["team"]=row["team"]
        p["games"].append({k:row[k] for k in ("game_id","date","values","home_away","position_group") if k in row})
    for p in players.values():p["games"].sort(key=lambda g:(g["date"],g["game_id"]))
    sog=[g["values"]["Shots on goal"] for p in players.values() for g in p["games"] if "Shots on goal" in g["values"]]
    if not sog or not any(x>0 for x in sog):
        raise SystemExit(f"NHL SOG sanity check failed: records={len(sog)} nonzero={sum(x>0 for x in sog)} parsed_games={parsed} checked={checked} sample_errors={errors[:3]}; official snapshot not overwritten")
    output={"source":"nhl-official-boxscore","sport":"nhl","fetched_at":datetime.now(timezone.utc).isoformat(),
            "completed_games_checked":checked,"games_parsed":parsed,"errors":errors[:100],
            "sog_observations":len(sog),"sog_nonzero":sum(x>0 for x in sog),
            "players":sorted(players.values(),key=lambda p:p["name"])}
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(output,separators=(",",":"))+"\n")
    print(f"NHL OFFICIAL: players={len(players)}, games={parsed}/{checked}, SOG records={len(sog)}, nonzero={sum(x>0 for x in sog)}, errors={len(errors)}")
if __name__=="__main__":sys.exit(main())
