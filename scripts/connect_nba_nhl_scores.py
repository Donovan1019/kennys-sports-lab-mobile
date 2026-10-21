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
        # Incrementally extend previously verified history with ESPN's supported
        # single-date scoreboard query (YYYYMMDD). Avoid unsupported date ranges.
        old_path=Path(f"feed/{league}_completed_games.json")
        old=json.loads(old_path.read_text()).get("games",[]) if old_path.exists() else []
        games=list(old)
        valid_dates=[g["date"][:10] for g in old if g.get("date")]
        last_seen=date.fromisoformat(max(valid_dates)) if valid_dates else date(now.year-1,1,1)
        # Repair missing historical months in bounded batches, rather than
        # assuming a recent last_seen date implies complete historical coverage.
        monthly_counts={}
        for stamp in valid_dates:
            month=stamp[:7]
            monthly_counts[month]=monthly_counts.get(month,0)+1
        missing_months=[]
        month=date(now.year-1,1,1)
        while month<=now.date().replace(day=1):
            key=month.strftime("%Y-%m")
            # Only flag regular-season core months; offseason and preseason
            # are legitimately empty. October and April are partial months.
            core_month=month.month in (11,12,1,2,3)
            threshold=40 if league=="nba" else 25
            if core_month and month<now.date().replace(day=1) and monthly_counts.get(key,0)<threshold:
                missing_months.append(month)
            month=(month.replace(day=28)+timedelta(days=4)).replace(day=1)
        # Recover the earliest sparse regular-season month per run to restore chronology.
        if missing_months:
            cursor=missing_months[0]
            next_month=(cursor.replace(day=28)+timedelta(days=4)).replace(day=1)
            stop=min(next_month-timedelta(days=1),now.date())
            print(f"{league}: recovering sparse month {cursor:%Y-%m}",flush=True)
        else:
            cursor=max(date(now.year-1,1,1),last_seen-timedelta(days=2))
            stop=now.date()
        failures=[]
        while cursor<=stop:
            stamp=cursor.strftime("%Y%m%d")
            url=f"https://site.api.espn.com/apis/site/v2/sports/{category}/{league}/scoreboard?dates={stamp}"
            for attempt in range(3):
                try:
                    req=urllib.request.Request(url,headers={"User-Agent":"KennysSportsLab/1.0","Accept":"application/json"})
                    with urllib.request.urlopen(req,timeout=25) as response:
                        payload=json.load(response)
                    if not isinstance(payload.get("events"),list):raise ValueError("Missing events")
                    games.extend(parse_league(payload))
                    break
                except (OSError,ValueError) as exc:
                    if attempt==2:failures.append({"date":stamp,"error":type(exc).__name__})
                    else:time.sleep(attempt+1)
            cursor+=timedelta(days=1)
        if failures:
            raise RuntimeError(f"{league}: {len(failures)} daily scoreboards failed; prior published feed preserved: {failures[:5]}")
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
