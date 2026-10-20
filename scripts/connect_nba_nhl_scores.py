"""Import independent NBA/NHL regular-season game scores from free ESPN endpoints."""
import json,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from scripts.connect_nfl_team_scores import parse_scoreboard,assemble
from scripts.backtest_nfl import evaluate

LEAGUES={"nba":("basketball","basketball_nba"),"nhl":("hockey","icehockey_nhl")}
def parse_league(data):
    return [g for event in data.get("events",[]) if str((event.get("season") or {}).get("type"))=="2" for g in parse_scoreboard({"events":[event]})]
def build_inputs(games,odds,sport,now):
    rows=[{**r,"sport":"americanfootball_nfl"} for r in odds.get("odds",[]) if r.get("sport")==sport]
    out=assemble(games,{"odds":rows},now)
    for g in out["games"]:g["sport"]=sport
    return out
def main():
    now=datetime.now(timezone.utc)
    for league,(category,sport) in LEAGUES.items():
        games=[]
        for year in (now.year-1,now.year):
            url=f"https://site.api.espn.com/apis/site/v2/sports/{category}/{league}/scoreboard?dates={year}&limit=1000"
            req=urllib.request.Request(url,headers={"User-Agent":"KennysSportsLab/1.0"})
            with urllib.request.urlopen(req,timeout=60) as response:games.extend(parse_league(json.load(response)))
        games=list({(g["date"],g["away"],g["home"]):g for g in games}.values())
        games.sort(key=lambda x:x["date"])
        if not games:raise RuntimeError(f"No verified {league} games")
        Path(f"feed/{league}_completed_games.json").write_text(json.dumps({"source":"espn-public-completed-league-games","league":league,"fetched_at":now.isoformat(),"games":games},indent=2)+"\n")
        odds_path=Path(f"feed/{sport}.json")
        odds=json.loads(odds_path.read_text()) if odds_path.exists() else {"odds":[]}
        inputs=build_inputs(games,odds,sport,now.isoformat())
        Path(f"feed/{league}_independent_game_inputs.json").write_text(json.dumps(inputs,indent=2)+"\n")
        report=evaluate(games,trials=10000)
        Path(f"feed/{league}_backtest.json").write_text(json.dumps({"source":"walk-forward-league-monte-carlo","league":league,"generated_at":now.isoformat(),**report},indent=2)+"\n")
        print(league.upper(),"completed:",len(games),"backtest:",report["sample_size"],"Brier:",report["brier"],"passed:",report["passed"],"eligible odds events:",len(inputs["games"]))
if __name__=="__main__":main()
