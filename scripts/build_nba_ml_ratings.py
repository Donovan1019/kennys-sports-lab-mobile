#!/usr/bin/env python3
"""ESPN public scoreboard ingestion, chronological Elo, walk-forward validation."""
import datetime as dt, json, math, os, pathlib, urllib.request
from zoneinfo import ZoneInfo

NBA_TEAMS={"Atlanta Hawks","Boston Celtics","Brooklyn Nets","Charlotte Hornets","Chicago Bulls","Cleveland Cavaliers","Dallas Mavericks","Denver Nuggets","Detroit Pistons","Golden State Warriors","Houston Rockets","Indiana Pacers","LA Clippers","Los Angeles Lakers","Memphis Grizzlies","Miami Heat","Milwaukee Bucks","Minnesota Timberwolves","New Orleans Pelicans","New York Knicks","Oklahoma City Thunder","Orlando Magic","Philadelphia 76ers","Phoenix Suns","Portland Trail Blazers","Sacramento Kings","San Antonio Spurs","Toronto Raptors","Utah Jazz","Washington Wizards"}
ROOT=pathlib.Path("data"); CACHE=ROOT/"nba_ml_historical_games.json"; OUT=ROOT/"nba_ml_validated_ratings.json"
URL="https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={day}&limit=100"
def day_games(day):
    req=urllib.request.Request(URL.format(day=day.strftime("%Y%m%d")),headers={"User-Agent":"KSL-NBA-Model/1.0"})
    with urllib.request.urlopen(req,timeout=15) as response: data=json.load(response)
    games=[]
    for event in data.get("events",[]):
        try:
            comp=event["competitions"][0]
            if not comp["status"]["type"].get("completed"):continue
            teams=comp["competitors"]
            home=next(t for t in teams if t["homeAway"]=="home")
            away=next(t for t in teams if t["homeAway"]=="away")
            hs=float(home["score"]);ats=float(away["score"])
            if hs==ats or home["team"]["displayName"] not in NBA_TEAMS or away["team"]["displayName"] not in NBA_TEAMS:continue
            games.append({"id":str(event["id"]),"date":event["date"],"home":home["team"]["displayName"],"away":away["team"]["displayName"],"home_win":int(hs>ats)})
        except (KeyError,IndexError,StopIteration,TypeError,ValueError):continue
    return games
def predict(diff):return 1/(1+math.exp(-max(-30,min(30,diff/173.7178))))
def fit(games):
    ratings={}; evaluated=[]; n=0
    for g in sorted(games,key=lambda x:(x["date"],x["id"])):
        if g["home"] not in NBA_TEAMS or g["away"] not in NBA_TEAMS:continue
        h,a=g["home"],g["away"];rh=ratings.get(h,1500.0);ra=ratings.get(a,1500.0)
        p=predict(rh-ra+60)
        if n>=200:evaluated.append((p,g["home_win"]))
        change=20*(g["home_win"]-p)
        ratings[h]=rh+change;ratings[a]=ra-change;n+=1
    if len(ratings)!=30 or len(evaluated)<100:raise ValueError("Insufficient games or teams for walk-forward evaluation")
    brier=sum((p-y)**2 for p,y in evaluated)/len(evaluated)
    buckets=[[] for _ in range(10)]
    for p,y in evaluated:buckets[min(9,int(p*10))].append((p,y))
    ece=sum(len(b)/len(evaluated)*abs(sum(p for p,y in b)/len(b)-sum(y for p,y in b)/len(b)) for b in buckets if b)
    if brier>=0.25 or ece>0.10:raise ValueError(f"Walk-forward calibration failed: Brier={brier:.4f}, ECE={ece:.4f}")
    return ratings,{"walk_forward_games":len(evaluated),"brier":round(brier,5),"ece":round(ece,5),"method":"chronological Elo, 200-game burn-in, no odds inputs"}
def main():
    ROOT.mkdir(exist_ok=True);today=dt.datetime.now(ZoneInfo("America/New_York")).date()
    # Prior full NBA regular season and current season; dates are cached to avoid repeat network calls.
    start=dt.date(2025,10,21);end=today-dt.timedelta(days=1)
    cache=json.loads(CACHE.read_text()) if CACHE.exists() else {"days":{}}
    days=cache.get("days",{});failures=[]
    d=start
    while d<=end:
        if d.month in (5,6,7,8,9) or (d.month==10 and d.day<20):
            d+=dt.timedelta(days=1);continue
        key=d.isoformat()
        if key not in days:
            try:days[key]=day_games(d)
            except Exception as exc:failures.append(f"{key}: {exc}")
        d+=dt.timedelta(days=1)
    CACHE.write_text(json.dumps({"days":days},separators=(",",":"))+"\n")
    # Reject historical non-NBA exhibition events, including entries already cached.
    for key in list(days):
        days[key]=[g for g in days[key] if g.get("home") in NBA_TEAMS and g.get("away") in NBA_TEAMS]
    CACHE.write_text(json.dumps({"days":days},separators=(",",":"))+"\\n")
    if failures:raise RuntimeError(f"Historical ingestion incomplete ({len(failures)} days): "+failures[0])
    all_games={g["id"]:g for day in days.values() for g in day}
    ratings,report=fit(list(all_games.values()))
    latest=max(g["date"] for g in all_games.values())
    result={"status":"validated","calibration_passed":True,"season":"2026-27","model_version":"elo-walkforward-v1","training_cutoff":latest,"validation_report":report,"teams":ratings,"home_advantage":60,"logistic_scale":173.7178}
    OUT.write_text(json.dumps(result,indent=2)+"\n")
    print("Validated NBA ratings:",len(ratings),"teams",report)
if __name__=="__main__":main()
