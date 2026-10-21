"""Import independent NBA/NHL regular-season game scores from free ESPN endpoints."""
import json,urllib.request,time,random
from datetime import date,timedelta
from datetime import datetime,timezone
from pathlib import Path
from scripts.connect_nfl_team_scores import parse_scoreboard,assemble
from scripts.backtest_nfl import evaluate
from scripts.matchup_monte_carlo import build_forecasts

LEAGUES={"nba":("basketball","basketball_nba"),"nhl":("hockey","icehockey_nhl")}
def parse_league(data):
    return [g for event in data.get("events",[]) if str((event.get("season") or {}).get("type"))=="2" for g in parse_scoreboard({"events":[event]})]
def build_inputs(games,odds,sport,now,upcoming=None):
    rows=[{**r,"sport":"americanfootball_nfl"} for r in odds.get("odds",[]) if r.get("sport")==sport]
    out=assemble(games,{"odds":rows},now,upcoming=upcoming)
    for g in out["games"]:g["sport"]=sport
    return out
def main():
    now=datetime.now(timezone.utc)
    for league,(category,sport) in LEAGUES.items():
        games=[]
        # ESPN annual scoreboard requests can silently truncate at their event limit.
        # Query bounded calendar windows and fail closed if any window is unavailable.
        first=date(now.year-1,1,1)
        last=now.date()
        cursor=first
        failures=[]
        while cursor<=last:
            end=min(cursor+timedelta(days=13),last)
            dates=cursor.strftime("%Y%m%d")+"-"+end.strftime("%Y%m%d")
            url=f"https://site.api.espn.com/apis/site/v2/sports/{category}/{league}/scoreboard?dates={dates}&limit=500"
            for attempt in range(3):
                try:
                    req=urllib.request.Request(url,headers={"User-Agent":"KennysSportsLab/1.0","Accept":"application/json"})
                    with urllib.request.urlopen(req,timeout=60) as response:
                        payload=json.load(response)
                    if not isinstance(payload.get("events"),list):raise ValueError("Missing events")
                    games.extend(parse_league(payload))
                    break
                except (OSError,ValueError) as exc:
                    if attempt==2:failures.append({"window":dates,"error":type(exc).__name__})
                    else:time.sleep(1.5*(attempt+1))
            cursor=end+timedelta(days=1)
        if failures:
            raise RuntimeError(f"{league}: {len(failures)} scoreboard windows failed; preserving prior published feed: {failures[:5]}")
        games=list({(g["date"],g["away"],g["home"]):g for g in games}.values())
        games.sort(key=lambda x:x["date"])
        if not games:raise RuntimeError(f"No verified {league} games")
        Path(f"feed/{league}_completed_games.json").write_text(json.dumps({"source":"espn-public-completed-league-games","league":league,"fetched_at":now.isoformat(),"games":games},indent=2)+"\n")
        odds_path=Path(f"feed/{sport}.json")
        odds=json.loads(odds_path.read_text()) if odds_path.exists() else {"odds":[]}
        # Verify future tipoff/puck drop independently of sportsbook snapshot.
        schedule_url=f"https://site.api.espn.com/apis/site/v2/sports/{category}/{league}/scoreboard"
        with urllib.request.urlopen(urllib.request.Request(schedule_url,headers={"User-Agent":"KennysSportsLab/1.0"}),timeout=60) as response:schedule=json.load(response)
        upcoming=set()
        for event in schedule.get("events",[]):
            try:
                tip=datetime.fromisoformat(event["date"].replace("Z","+00:00"))
                sides=event["competitions"][0]["competitors"]
                away=next(x["team"]["displayName"] for x in sides if x["homeAway"]=="away")
                home=next(x["team"]["displayName"] for x in sides if x["homeAway"]=="home")
                if tip>now:upcoming.add((away,home))
            except (KeyError,ValueError,TypeError,StopIteration):continue
        inputs=build_inputs(games,odds,sport,now.isoformat(),upcoming=upcoming)
        Path(f"feed/{league}_independent_game_inputs.json").write_text(json.dumps(inputs,indent=2)+"\n")
        # NHL settlement includes OT/shootouts: continuous-score MC is not a valid NHL moneyline engine.
        report=evaluate(games,trials=10000,sport=sport)
        report["production_ready"]=False
        report["limitations"]=(["Overtime/shootout outcomes not explicitly modeled","Spread and total markets not independently validated"] if league=="nhl" else ["Spread and total markets not independently validated","No independently verified market-specific calibration"])
        if odds.get("source")=="the-odds-api-v4" and inputs["games"]:
            candidates=build_forecasts(inputs,odds)
        else:
            candidates={"schema_version":1,"predictions":[],"model_status":"experimental-no-eligible-odds"}
        Path(f"feed/{league}_model_candidates.json").write_text(json.dumps(candidates,indent=2)+"\n")
        Path(f"feed/{league}_backtest.json").write_text(json.dumps({"source":"walk-forward-league-monte-carlo","league":league,"generated_at":now.isoformat(),**report},indent=2)+"\n")
        print(league.upper(),"completed:",len(games),"backtest:",report["sample_size"],"Brier:",report["brier"],"passed:",report["passed"],"eligible odds events:",len(inputs["games"]))
if __name__=="__main__":main()
