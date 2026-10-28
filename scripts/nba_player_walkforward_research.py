#!/usr/bin/env python3
"""Strictly chronological NBA player stat research backtest; never emits picks."""
import json, math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

SOURCE=Path("feed/nba_player_stats.json")
OUTPUT=Path("feed/nba_player_walkforward_research.json")
MARKETS=("Points","Rebounds","Assists","Threes")
MIN_PRIOR=8

def evaluate(data):
    if not isinstance(data,dict) or data.get("source")!="espn-public-boxscore" or data.get("sport")!="nba":
        raise ValueError("Verified NBA player game-log source required")
    players=data.get("players")
    if not isinstance(players,list): raise ValueError("Missing player game logs")
    totals=defaultdict(lambda:{"n":0,"abs_error":0.0,"squared_error":0.0,"baseline_abs_error":0.0,"by_season":{}})
    seen=set()
    for player in players:
        if not isinstance(player,dict): continue
        pid=str(player.get("id",""))
        if not pid: continue
        games=player.get("games") or []
        if not isinstance(games,list): continue
        valid=[]
        for game in games:
            if not isinstance(game,dict): continue
            day=game.get("date");gid=str(game.get("game_id",""))
            values=game.get("values")
            if not isinstance(day,str) or not gid or not isinstance(values,dict): continue
            if not isinstance(game.get("season"),str) or game.get("season_type") not in ("regular","postseason"):continue
            try: datetime.strptime(day,"%Y-%m-%d")
            except ValueError:continue
            if (pid,gid) in seen:continue
            seen.add((pid,gid))
            valid.append((day,gid,game["season"],values))
        valid.sort(key=lambda g:(g[0],g[1]))
        for market in MARKETS:
            history=[]
            for day,gid,season,values in valid:
                actual=values.get(market)
                if not isinstance(actual,(int,float)) or isinstance(actual,bool) or not math.isfinite(actual) or actual<0:continue
                # A same-day result cannot be used to predict another game on that day.
                prior=[v for d,v in history if d<day]
                if len(prior)>=MIN_PRIOR:
                    recent=prior[-10:]
                    prediction=sum(recent)/len(recent)
                    baseline=sum(prior)/len(prior)
                    record=totals[market]
                    record["n"]+=1
                    record["abs_error"]+=abs(prediction-actual)
                    record["squared_error"]+=(prediction-actual)**2
                    record["baseline_abs_error"]+=abs(baseline-actual)
                    season_count=record["by_season"].setdefault(season,0)
                    record["by_season"][season]=season_count+1
                history.append((day,float(actual)))
    metrics={}
    for market,record in totals.items():
        n=record["n"]
        metrics[market]={"samples":n,"mae_last_10":round(record["abs_error"]/n,4),
            "rmse_last_10":round(math.sqrt(record["squared_error"]/n),4),
            "mae_all_prior_baseline":round(record["baseline_abs_error"]/n,4),
            "samples_by_season":record["by_season"]}
    return {"status":"research_only","promotion_approved":False,
        "method":"strict-prior-date-walk-forward-player-rolling-mean",
        "minimum_prior_games":MIN_PRIOR,
        "markets":metrics,
        "warning":"Point-in-time sportsbook lines, injury/lineup context, calibration, joint SGP probability and independent validation are unavailable. This is NOT a bet recommendation."}

def main():
    data=json.loads(SOURCE.read_text())
    result=evaluate(data)
    result["generated_at"]=datetime.now(timezone.utc).isoformat()
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"markets":result["markets"]}))

if __name__=="__main__":main()
