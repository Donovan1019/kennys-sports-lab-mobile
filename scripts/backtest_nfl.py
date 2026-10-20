"""Leakage-resistant chronological NFL scoring model evaluation.
Each prediction uses only games strictly before kickoff. No market prices used.
"""
import json,math,random,statistics
from datetime import datetime,timezone
from pathlib import Path
from scripts.connect_nfl_team_scores import team_parameters
from scripts.matchup_monte_carlo import simulate_game

def evaluate(games,*,trials=10000,minimum=100):
    ordered=sorted(games,key=lambda g:g["date"])
    results=[]
    for i,g in enumerate(ordered):
        past=ordered[:i]
        away=team_parameters(past,g["away"],g["date"])
        home=team_parameters(past,g["home"],g["date"])
        if not away or not home:continue
        am=(away["for_mean"]+home["against_mean"])/2
        hm=(home["for_mean"]+away["against_mean"])/2
        ads=math.sqrt((away["for_sd"]**2+home["against_sd"]**2)/2)
        hds=math.sqrt((home["for_sd"]**2+away["against_sd"]**2)/2)
        sim=simulate_game(am,hm,ads,hds,trials=trials,seed=1000+i)
        decisive=[(a,h) for a,h in sim if abs(a-h)>1e-9]
        if not decisive:continue
        p=sum(h>a for a,h in decisive)/len(decisive)
        if g["away_score"]==g["home_score"]:continue
        y=int(g["home_score"]>g["away_score"])
        results.append({"date":g["date"],"event_id":g.get("event_id"),"home":g["home"],"away":g["away"],
                        "predicted_home_win":p,"actual_home_win":y,
                        "home_projected_points":hm,"away_projected_points":am,
                        "actual_home_points":g["home_score"],"actual_away_points":g["away_score"],
                        "squared_error":(p-y)**2})
    n=len(results)
    brier=sum(r["squared_error"] for r in results)/n if n else None
    base=sum(r["actual_home_win"] for r in results)/n if n else None
    baseline=base*(1-base) if base is not None else None
    mae=sum((abs(r["home_projected_points"]-r["actual_home_points"])+abs(r["away_projected_points"]-r["actual_away_points"]))/2 for r in results)/n if n else None
    bins=[]
    for low in (0,.2,.4,.6,.8):
        selected=[r for r in results if low<=r["predicted_home_win"]<(low+.2 if low<.8 else 1.00001)]
        bins.append({"range":[low,round(low+.2,1)],"n":len(selected),"mean_predicted":statistics.mean(r["predicted_home_win"] for r in selected) if selected else None,"actual_rate":statistics.mean(r["actual_home_win"] for r in selected) if selected else None})
    passed=n>=minimum and brier is not None and baseline is not None and brier<baseline
    return {"method":"walk_forward","model_version":"independent-scoring-mc-v1","sample_size":n,"trials_per_game":trials,
            "brier":brier,"constant_home_baseline_brier":baseline,"mean_team_score_absolute_error":mae,
            "passed":passed,"criteria":"at least 100 strictly chronological out-of-sample games and Brier lower than constant home-win baseline",
            "calibration_bins":bins,"evaluation_start":results[0]["date"] if results else None,
            "evaluation_end":results[-1]["date"] if results else None,
            "results":results}

def main():
    path=Path("feed/nfl_completed_games.json")
    if not path.exists():raise SystemExit("Missing verified completed-game feed")
    data=json.loads(path.read_text())
    if data.get("source")!="espn-public-completed-nfl-games":raise ValueError("Unverified game feed")
    report=evaluate(data["games"])
    Path("feed/nfl_backtest.json").write_text(json.dumps({"source":"walk-forward-nfl-monte-carlo","generated_at":datetime.now(timezone.utc).isoformat(),**report},indent=2)+"\n")
    print("Walk-forward games:",report["sample_size"],"Brier:",report["brier"],"baseline:",report["constant_home_baseline_brier"],"passed:",report["passed"])
if __name__=="__main__":main()
