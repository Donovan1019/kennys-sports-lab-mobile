#!/usr/bin/env python3
"""Chronological, out-of-sample NBA possession ML validation. Never promote without evidence."""
import datetime as dt
import json
import pathlib
from scripts.simulate_nba_ml_possessions import metrics, simulate

SOURCE=pathlib.Path("data/nba_ml_possession_boxscores.json")
OUT=pathlib.Path("feed/nba_ml_possession_backtest.json")
def evaluate(games,min_history=15,min_holdout=100):
    ordered=sorted(games,key=lambda g:(g.get("date",""),str(g.get("id",""))))
    results=[]
    for game in ordered:
        try:
            tip=dt.datetime.fromisoformat(game["date"].replace("Z","+00:00"))
            earlier=[g for g in ordered if g.get("date","")<game["date"]]
            teams=metrics(earlier,tip,min_games=min_history)
            prediction=simulate(game["home"],game["away"],teams,str(game["id"]),draws=1000)
            if prediction["status"]!="diagnostic_only":continue
            # Regulation ties are not modeled as NBA final ML outcomes; reject these
            # predictions for betting calibration until overtime is implemented.
            if prediction["regulation_tie_probability"]>0:continue
            home_points=game["box"][game["home"]]["points"]
            away_points=game["box"][game["away"]]["points"]
            if home_points==away_points:continue
            results.append((prediction["home_regulation_win_probability"],int(home_points>away_points)))
        except (KeyError,ValueError,TypeError):continue
    report={"status":"insufficient_evidence","evaluated_games":len(results),"minimum_holdout_games":min_holdout,"betting_eligible":False,"blockers":["overtime_unmodeled","historical_validation_unverified"]}
    if len(results)>=min_holdout:
        report.update({"status":"descriptive_only","brier":round(sum((p-y)**2 for p,y in results)/len(results),6),"accuracy":round(sum((p>=.5)==bool(y) for p,y in results)/len(results),6)})
    return report
def main():
    try:games=json.loads(SOURCE.read_text()).get("games",[])
    except (OSError,ValueError):games=[]
    report=evaluate(games)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2)+"\n")
    print(report)
if __name__=="__main__":main()
