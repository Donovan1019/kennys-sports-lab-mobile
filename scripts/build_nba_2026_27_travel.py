#!/usr/bin/env python3
"""Build scheduled NBA 2026-27 back-to-backs from NBA's official league schedule.
No betting picks or unverified point spreads are generated.
"""
import json
import urllib.request
from datetime import datetime, date
from pathlib import Path

URLS=[
 "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json",
 "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json",
]
CITY={"ATL":"Atlanta","BOS":"Boston","BKN":"Brooklyn, NY","CHA":"Charlotte","CHI":"Chicago","CLE":"Cleveland","DAL":"Dallas","DEN":"Denver","DET":"Detroit","GSW":"San Francisco","HOU":"Houston","IND":"Indianapolis","LAC":"Inglewood, CA","LAL":"Los Angeles","MEM":"Memphis","MIA":"Miami","MIL":"Milwaukee","MIN":"Minneapolis","NOP":"New Orleans","NYK":"New York","OKC":"Oklahoma City","ORL":"Orlando","PHI":"Philadelphia","PHX":"Phoenix","POR":"Portland, OR","SAC":"Sacramento","SAS":"San Antonio","TOR":"Toronto","UTA":"Salt Lake City","WAS":"Washington, DC"}

def schedule():
    """ESPN public calendar fallback: one request per team, deduplicate event IDs."""
    errors=[]
    for url in URLS:
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req,timeout=25) as resp:
                payload=json.load(resp)
            league=payload.get("leagueSchedule") or payload.get("schedule") or {}
            games=[]
            for group in league.get("gameDates") or []:
                for game in group.get("games",[]):
                    home=(game.get("homeTeam") or {}).get("teamTricode")
                    away=(game.get("awayTeam") or {}).get("teamTricode")
                    stamp=game.get("gameDateEst") or group.get("gameDate") or game.get("gameDateTimeEst")
                    if home and away and stamp:
                        dt=str(stamp)[:10]
                        if "2026-10-20"<=dt<="2027-04-11":
                            games.append({"date":dt,"home":home,"away":away,"game_id":str(game.get("gameId") or "")})
            if len(games)>=1000:return games,url
            errors.append(f"NBA CDN incomplete ({len(games)} games)")
        except Exception as exc:errors.append(f"NBA CDN: {exc}")
    import time
    from zoneinfo import ZoneInfo
    teams=list(CITY)
    found={}
    for team in teams:
        url=f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team.lower()}/schedule?season=2027&seasontype=2&limit=100"
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=25) as resp:
                data=json.load(resp)
            for event in data.get("events") or []:
                eid=str(event.get("id") or "")
                competition=(event.get("competitions") or [{}])[0]
                competitors=competition.get("competitors") or []
                home=next((x for x in competitors if x.get("homeAway")=="home"),None)
                away=next((x for x in competitors if x.get("homeAway")=="away"),None)
                if not home or not away:continue
                h=(home.get("team") or {}).get("abbreviation","").upper()
                a=(away.get("team") or {}).get("abbreviation","").upper()
                h={"NY":"NYK","GS":"GSW","SA":"SAS","NO":"NOP","UTAH":"UTA"}.get(h,h)
                a={"NY":"NYK","GS":"GSW","SA":"SAS","NO":"NOP","UTAH":"UTA"}.get(a,a)
                if h not in CITY or a not in CITY:continue
                stamp=event.get("date")
                if not stamp:continue
                dt=datetime.fromisoformat(stamp.replace("Z","+00:00")).astimezone(ZoneInfo("America/New_York")).date().isoformat()
                if "2026-10-20"<=dt<="2027-04-11":
                    found[eid or f"{dt}-{h}-{a}"]={"date":dt,"home":h,"away":a,"game_id":eid}
        except Exception as exc:errors.append(f"ESPN {team}: {exc}")
        time.sleep(.1)
    if len(found)<1000:
        raise RuntimeError(f"NBA schedule incomplete ({len(found)} games); refusing to publish. Errors: {errors[:6]}")
    return list(found.values()),"ESPN public NBA team schedules (NBA league schedule cross-reference)"

def build(games):
    last={};out=[]
    for game in sorted(games,key=lambda x:x["date"]):
        day=date.fromisoformat(game["date"])
        for side in ("home","away"):
            team=game[side];old=last.get(team)
            if old and (day-old["date"]).days==1:
                frm=CITY.get(old["venue"],old["venue"]);to=CITY.get(game["home"],game["home"])
                out.append({"previous_date":old["date"].isoformat(),"date":game["date"],"team":team,"opponent":game["away" if side=="home" else "home"],"from":frm,"to":to,"from_venue":old["venue"],"to_venue":game["home"],"changed_venue":old["venue"]!=game["home"],"pattern":old["side"]+" → "+side,"game_id":game["game_id"],"status":"SCHEDULED"})
            last[team]={"date":day,"venue":game["home"],"side":side}
    return out

if __name__=="__main__":
    games,source=schedule()
    rows=build(games)
    result={"season":"2026-27","source":source,"updated_at":datetime.now().astimezone().isoformat(),"games_in_schedule":len(games),"upcoming_b2b":rows,"note":"Scheduled arena locations inferred from home team. NBA Cup dates and exceptional venues may change. No ATS predictions."}
    out=Path("feed/nba_2026_27_b2b.json");out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(f"Wrote {len(rows)} back-to-back appearances from {len(games)} NBA scheduled games")
