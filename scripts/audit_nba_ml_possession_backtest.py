#!/usr/bin/env python3
"""Chronological, out-of-sample NBA possession ML validation. Never promote without evidence."""
import datetime as dt
import json
import math
import pathlib
from scripts.simulate_nba_ml_possessions import metrics, simulate

SOURCE=pathlib.Path("data/nba_ml_possession_boxscores.json")
OUT=pathlib.Path("feed/nba_ml_possession_backtest.json")
def evaluate(games,min_history=15,min_holdout=100):
    ordered=sorted(games,key=lambda g:(g.get("date",""),str(g.get("id",""))))
    results=[]
    for index,game in enumerate(ordered):
        try:
            tip=dt.datetime.fromisoformat(game["date"].replace("Z","+00:00"))
            earlier=[g for g in ordered[:index] if g.get("date","")<game["date"]]
            teams=metrics(earlier,tip,min_games=min_history)
            prediction=simulate(game["home"],game["away"],teams,str(game["id"]),draws=500)
            if prediction["status"]!="diagnostic_only":continue
            probability=prediction["home_full_game_win_probability"]
            if (not isinstance(probability,(int,float)) or isinstance(probability,bool)
                    or not math.isfinite(probability) or not 0<=probability<=1):
                continue
            home_points=game["box"][game["home"]]["points"]
            away_points=game["box"][game["away"]]["points"]
            if home_points==away_points:continue
            results.append((probability,int(home_points>away_points)))
        except (KeyError,ValueError,TypeError):continue
    report={"status":"insufficient_evidence","evaluated_games":len(results),"minimum_holdout_games":min_holdout,"betting_eligible":False,"blockers":["overtime_approximation_unvalidated","historical_validation_unverified"]}
    if len(results)>=min_holdout:
        brier=sum((p-y)**2 for p,y in results)/len(results)
        log_loss=-sum(y*math.log(max(1e-9,min(1-1e-9,p)))+(1-y)*math.log(max(1e-9,min(1-1e-9,1-p))) for p,y in results)/len(results)
        report.update({"status":"descriptive_only","brier":round(brier,6),"log_loss":round(log_loss,6),"accuracy":round(sum((p>=.5)==bool(y) for p,y in results)/len(results),6)})
        report["calibration_bins"]=[]
        for lo in range(0,100,10):
            sample=[(p,y) for p,y in results if lo/100<=p<(lo+10)/100 or (lo==90 and p==1)]
            if not sample:continue
            n=len(sample)
            observed=sum(y for _,y in sample)/n
            z=1.96
            denominator=1+z*z/n
            center=(observed+z*z/(2*n))/denominator
            half=z*math.sqrt(observed*(1-observed)/n+z*z/(4*n*n))/denominator
            report["calibration_bins"].append({"range":[lo/100,(lo+10)/100],"count":n,"mean_predicted":round(sum(p for p,_ in sample)/n,6),"observed_win_rate":round(observed,6),"observed_wilson_95":[round(max(0,center-half),6),round(min(1,center+half),6)]})
        report["baseline"]={"constant_home_win_rate":round(sum(y for _,y in results)/len(results),6),"constant_brier":round(sum((sum(y for _,y in results)/len(results)-y)**2 for _,y in results)/len(results),6),"warning":"In-sample constant-rate comparator, not a point-in-time bookmaker or independent out-of-sample baseline."}
        report["calibration_coverage"]={"total_evaluated":len(results),"binned_games":sum(b["count"] for b in report["calibration_bins"]),"excluded_games":len(results)-sum(b["count"] for b in report["calibration_bins"]),"small_sample_bins":[b["range"] for b in report["calibration_bins"] if b["count"]<50],"minimum_bin_sample_warning":50}
        # Strictly forward-scored constant baseline: each game's baseline uses only
        # earlier evaluated outcomes, never the outcome being scored.
        forward=[]
        prior_wins=0
        for i,(p,y) in enumerate(results):
            if i>=min_holdout:
                baseline_probability=prior_wins/i
                forward.append((p,y,baseline_probability))
            prior_wins+=y
        if len(forward)>=min_holdout:
            def score(probability,outcome):
                q=max(1e-9,min(1-1e-9,probability))
                return -outcome*math.log(q)-(1-outcome)*math.log(1-q)
            report["forward_baseline"]={
                "status":"descriptive_only",
                "warmup_games":min_holdout,
                "evaluated_games":len(forward),
                "model_brier":round(sum((p-y)**2 for p,y,_ in forward)/len(forward),6),
                "baseline_brier":round(sum((b-y)**2 for _,y,b in forward)/len(forward),6),
                "model_log_loss":round(sum(score(p,y) for p,y,_ in forward)/len(forward),6),
                "baseline_log_loss":round(sum(score(b,y) for _,y,b in forward)/len(forward),6),
                "warning":"Sequential past-only constant-rate baseline; neither independently frozen model validation nor bookmaker comparison."
            }
        else:
            report["forward_baseline"]={"status":"insufficient_evidence","warmup_games":min_holdout,"evaluated_games":len(forward)}
        report["calibration_warning"]="Chronological diagnostic only; Wilson intervals reflect binomial sampling uncertainty, not time dependence or model uncertainty. No independent market baseline, executed odds, or validated forward performance."

    return report
def main():
    try:games=json.loads(SOURCE.read_text()).get("games",[])
    except (OSError,ValueError):games=[]
    report=evaluate(games)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2)+"\n")
    print(report)
if __name__=="__main__":main()
