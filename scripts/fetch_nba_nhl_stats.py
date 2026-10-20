#!/usr/bin/env python3
"""Manual, free-first NBA/NHL player game-log importer from public ESPN JSON.
Not an official stable API; schema validated, no fabricated data, no predictions.
"""
import json, os, sys, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

LEAGUES={"nba":("basketball","nba"),"nhl":("hockey","nhl")}
MARKETS={"nba":{"PTS":"Points","REB":"Rebounds","AST":"Assists","3PT":"Threes","MIN":"Minutes","STL":"Steals","BLK":"Blocks","TO":"Turnovers"},
         "nhl":{"G":"Goals","A":"Assists","PTS":"Points","SOG":"Shots on goal","SV":"Saves"}}
def request(url):
    req=urllib.request.Request(url,headers={"User-Agent":"KennysSportsLab/1.0 (public research; contact via GitHub)","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=25) as res:
        raw=res.read(8_000_000)
        if res.read(1):raise ValueError("JSON response too large")
    return json.loads(raw)
def scalar(value):
    if isinstance(value,(int,float)):return float(value)
    if not isinstance(value,str):return None
    try:
        if ":" in value:
            a,b=value.split(":",1)
            return int(a)+int(b)/60
        if "-" in value:return float(value.split("-",1)[0])
        return float(value)
    except (ValueError,TypeError):return None
def parse_summary(data,league,game_id,game_date):
    if not isinstance(data,dict):raise ValueError("Invalid summary")
    box=data.get("boxscore") or {}
    players=box.get("players") or []
    if not isinstance(players,list):raise ValueError("Invalid players")
    output=[]
    for team in players:
        team_code=(team.get("team") or {}).get("abbreviation","")
        for group in team.get("statistics") or []:
            labels=group.get("labels") or []
            keys=group.get("keys") or []
            for entry in group.get("athletes") or []:
                athlete=entry.get("athlete") or {}
                ident=str(athlete.get("id") or "")
                name=athlete.get("displayName") or athlete.get("fullName")
                values=entry.get("stats") or []
                if not ident or not name or not isinstance(values,list):continue
                stats={}
                for i,raw in enumerate(values):
                    label=str(labels[i] if i<len(labels) else keys[i] if i<len(keys) else "").upper()
                    if league=="nba":
                        aliases={"PTS":"Points","POINTS":"Points","REB":"Rebounds","REBOUNDS":"Rebounds","AST":"Assists","ASSISTS":"Assists","3PT":"Threes","3PM":"Threes","3-PT":"Threes","MIN":"Minutes","MINUTES":"Minutes","STL":"Steals","STEALS":"Steals","BLK":"Blocks","BLOCKS":"Blocks","TO":"Turnovers","TURNOVERS":"Turnovers"}
                    else:
                        aliases={"G":"Goals","GOALS":"Goals","A":"Assists","AST":"Assists","PTS":"Points","SOG":"Shots on goal","SHOTS":"Shots on goal","SV":"Saves","SAVES":"Saves"}
                    metric=aliases.get(label)
                    val=scalar(raw)
                    if metric and val is not None and 0<=val<1000:stats[metric]=val
                if league=="nba":
                    if "Points" in stats and "Rebounds" in stats:stats["Pts+Reb"]=stats["Points"]+stats["Rebounds"]
                    if "Points" in stats and "Assists" in stats:stats["Pts+Ast"]=stats["Points"]+stats["Assists"]
                    if "Rebounds" in stats and "Assists" in stats:stats["Reb+Ast"]=stats["Rebounds"]+stats["Assists"]
                    if all(x in stats for x in ("Points","Rebounds","Assists")):
                        stats["PRA"]=stats["Points"]+stats["Rebounds"]+stats["Assists"]
                        double_digits=sum(stats[x]>=10 for x in ("Points","Rebounds","Assists"))
                        stats["Double-double (PTS/REB/AST)"]=int(double_digits>=2)
                        stats["Triple-double (PTS/REB/AST)"]=int(double_digits>=3)
                    if "Steals" in stats and "Blocks" in stats:stats["Stocks"]=stats["Steals"]+stats["Blocks"]
                if stats:output.append({"id":ident,"name":name,"team":team_code,"game_id":game_id,"date":game_date,"values":stats})
    return output
def main():
    league=os.getenv("PLAYER_SPORT","nba").lower()
    if league not in LEAGUES:raise ValueError("Choose nba or nhl")
    days=int(os.getenv("LOOKBACK_DAYS","7"))
    start_text=os.getenv("START_DATE","").strip()
    start_day=date.fromisoformat(start_text) if start_text else date.today()
    if start_day>date.today():raise ValueError("START_DATE cannot be in the future")
    if not 1<=days<=31:raise ValueError("Lookback limited to 1–31 days per batch")
    today=start_day
    path=Path("feed")/f"{league}_player_stats.json"
    prior={}
    if path.exists():
        old=json.loads(path.read_text())
        if old.get("source")=="espn-public-boxscore" and old.get("sport")==league:
            for p in old.get("players",[]):
                for g in p.get("games",[]):
                    prior[(str(p["id"]),str(g["game_id"]))]={"id":str(p["id"]),"name":p["name"],"team":p.get("team",""),**g}
    sport,code=LEAGUES[league]
    errors=[];scanned=0;parsed=0
    for offset in range(days):
        day=today-timedelta(days=offset)
        if league=="nba" and not (date(2025,10,1)<=day<=date.today()):continue
        stamp=day.strftime("%Y%m%d")
        base=f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{code}"
        try:
            schedule=request(f"{base}/scoreboard?dates={stamp}")
            events=schedule.get("events") or []
            if not isinstance(events,list):raise ValueError("Invalid schedule events")
        except Exception as exc:
            errors.append({"date":stamp,"error":type(exc).__name__});continue
        for event in events:
            state=((event.get("status") or {}).get("type") or {}).get("completed",False)
            gid=str(event.get("id") or "")
            if not gid or not state:continue
            season_meta=event.get("season") or {}
            season_type=(event.get("seasonType") or {}).get("type") or season_meta.get("type")
            # ESPN NBA season type 2 = regular season, 3 = postseason; exclude preseason.
            if league=="nba" and season_type is not None and str(season_type) not in ("2","3"):continue
            scanned+=1
            try:
                data=request(f"{base}/summary?event={gid}")
                rows=parse_summary(data,league,gid,day.isoformat())
                if not rows:raise ValueError("No usable athlete statistics")
                for row in rows:
                    if league=="nba":
                        row["season"]="2025-26" if day<date(2026,7,1) else "2026-27"
                        row["season_type"]="postseason" if str(season_type)=="3" else "regular"
                    prior[(row["id"],gid)]=row
                parsed+=1
            except Exception as exc:
                errors.append({"event":gid,"error":type(exc).__name__})
    if league=="nhl":
        # ESPN's SOG column has proven unreliable in the initial snapshot.
        # Remove it rather than publishing fabricated zero-shot histories.
        for row in prior.values():
            row["values"].pop("Shots on goal",None)
    if not prior:
        print(f"DIAGNOSTICS sport={league} lookback={days} completed_games={scanned} parsed_games={parsed} errors={len(errors)}",flush=True)
        print("SOURCE_ERRORS="+json.dumps(errors[:10]),flush=True)
        raise SystemExit("No verified player game logs; previous snapshot left unchanged")
    grouped={}
    for row in prior.values():
        if league=="nba" and not (row.get("season") in ("2025-26","2026-27") and row.get("season_type") in ("regular","postseason")):continue
        pid=row["id"];p=grouped.setdefault(pid,{"id":pid,"name":row["name"],"team":row["team"],"games":[]})
        p["name"]=row["name"];p["team"]=row["team"]
        p["games"].append({"game_id":row["game_id"],"date":row["date"],"season":row.get("season"),"season_type":row.get("season_type"),"values":row["values"]})
    if not grouped:raise SystemExit("No season-tagged regular/postseason player logs; preserving existing snapshot")
    for p in grouped.values():
        p["games"].sort(key=lambda g:(g["date"],g["game_id"]))
        if league=="nba":
            p["games"]=[g for g in p["games"] if g.get("season") in ("2025-26","2026-27") and g.get("season_type") in ("regular","postseason")]
    output={"source":"espn-public-boxscore","sport":league,"fetched_at":datetime.now(timezone.utc).isoformat(),
            "lookback_days":days,"batch_start_date":start_day.isoformat(),"seasons":["2025-26","2026-27"] if league=="nba" else [],"completed_games_checked":scanned,"games_parsed":parsed,
            "errors":errors[:100],"unverified_markets":(["Shots on goal"] if league=="nhl" else []),"players":sorted(grouped.values(),key=lambda p:p["name"])}
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(output,separators=(",",":"))+"\n")
    print(f"{league.upper()}: {len(grouped)} players; {parsed}/{scanned} completed games parsed; {len(errors)} errors")
    return 0
if __name__=="__main__":sys.exit(main())
