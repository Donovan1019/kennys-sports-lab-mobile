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
WINDOWS=(5,10,20,"all","blend_25","blend_50","blend_75")
TRAIN_SEASON="2025-26"
HOLDOUT_SEASON="2026-27"
MIN_TRAIN_SPLIT_SAMPLES=100
MIN_HOLDOUT_SAMPLES=1000
MIN_HOLDOUT_RELATIVE_IMPROVEMENT=0.01

def evaluate(data):
    if not isinstance(data,dict) or data.get("source")!="espn-public-boxscore" or data.get("sport")!="nba":
        raise ValueError("Verified NBA player game-log source required")
    players=data.get("players")
    if not isinstance(players,list): raise ValueError("Missing player game logs")
    training_error_records=defaultdict(list)
    window_errors=defaultdict(lambda:defaultdict(lambda:defaultdict(lambda:{"n":0,"absolute_error":0.0,"squared_error":0.0})))
    totals=defaultdict(lambda:{"n":0,"abs_error":0.0,"squared_error":0.0,"baseline_abs_error":0.0,"by_season":{}})
    holdout=defaultdict(lambda:defaultdict(lambda:{"n":0,"abs_error":0.0,"baseline_abs_error":0.0}))
    thresholds=defaultdict(lambda:defaultdict(lambda:{"n":0,"over":0,"under":0,"push":0}))
    probability_scores=defaultdict(lambda:defaultdict(lambda:{"n":0,"brier":0.0,"baseline_brier":0.0}))
    probability_by_season=defaultdict(lambda:defaultdict(lambda:defaultdict(lambda:{"n":0,"brier":0.0,"baseline_brier":0.0})))
    # Fixed research thresholds only: no sportsbook quote, vig, or wager eligibility.
    reference_lines={"Points":(9.5,19.5,29.5),"Rebounds":(4.5,7.5,10.5),
        "Assists":(3.5,5.5,8.5),"Threes":(1.5,2.5,3.5)}
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
                    for window in WINDOWS:
                        if isinstance(window,str) and window.startswith("blend_"):
                            weight=int(window.split("_")[1])/100
                            forecast=weight*prediction+(1-weight)*baseline
                        else:
                            sample=prior if window=="all" else prior[-window:]
                            forecast=sum(sample)/len(sample)
                        bucket=window_errors[market][season][str(window)]
                        bucket["n"]+=1
                        bucket["absolute_error"]+=abs(forecast-actual)
                        bucket["squared_error"]+=(forecast-actual)**2
                        if season==TRAIN_SEASON:
                            training_error_records[market].append((day,str(window),abs(forecast-actual)))
                    record=totals[market]
                    record["n"]+=1
                    record["abs_error"]+=abs(prediction-actual)
                    record["squared_error"]+=(prediction-actual)**2
                    record["baseline_abs_error"]+=abs(baseline-actual)
                    for line in reference_lines[market]:
                        if len(prior)>=MIN_PRIOR:
                            t=thresholds[market][str(line)]
                            t["n"]+=1
                            # Only games before this date may inform the estimated over probability.
                            earlier=[v for d,v in history if d<day]
                            prior_over=sum(v>line for v in earlier)
                            # Laplace-smoothed empirical probability, not calibrated sportsbook probability.
                            p=(prior_over+1)/(len(earlier)+2)
                            outcome=float(actual>line)
                            score=probability_scores[market][str(line)]
                            score["n"]+=1
                            score["brier"]+=(p-outcome)**2
                            score["baseline_brier"]+=(0.5-outcome)**2
                            season_score=probability_by_season[market][season][str(line)]
                            season_score["n"]+=1
                            season_score["brier"]+=(p-outcome)**2
                            season_score["baseline_brier"]+=(0.5-outcome)**2
                            if actual>line:t["over"]+=1
                            elif actual<line:t["under"]+=1
                            else:t["push"]+=1
                    block=holdout[market][season]
                    block["n"]+=1
                    block["abs_error"]+=abs(prediction-actual)
                    block["baseline_abs_error"]+=abs(baseline-actual)
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
    season_metrics={}
    for market,blocks in holdout.items():
        season_metrics[market]={season:{"samples":r["n"],"mae_last_10":round(r["abs_error"]/r["n"],4),
            "mae_all_prior_baseline":round(r["baseline_abs_error"]/r["n"],4)}
            for season,r in blocks.items() if r["n"]}
    threshold_metrics={market:{line:{"samples":v["n"],"over_rate":round(v["over"]/v["n"],4),
        "under_rate":round(v["under"]/v["n"],4),"pushes":v["push"]}
        for line,v in lines.items() if v["n"]} for market,lines in thresholds.items()}
    brier_metrics={market:{line:{"samples":v["n"],
        "walkforward_brier":round(v["brier"]/v["n"],5),
        "constant_50pct_brier":round(v["baseline_brier"]/v["n"],5)}
        for line,v in lines.items() if v["n"]} for market,lines in probability_scores.items()}
    season_probability_metrics={
        market:{season:{line:{"samples":r["n"],
            "walkforward_brier":round(r["brier"]/r["n"],5),
            "constant_50pct_brier":round(r["baseline_brier"]/r["n"],5),
            "beats_constant_50pct":r["brier"]<r["baseline_brier"]}
            for line,r in lines.items() if r["n"]}
            for season,lines in seasons.items()}
        for market,seasons in probability_by_season.items()}
    window_diagnostics={
        market:{season:{window:{"samples":r["n"],
            "mae":round(r["absolute_error"]/r["n"],4),
            "rmse":round(math.sqrt(r["squared_error"]/r["n"]),4)}
            for window,r in windows.items() if r["n"]}
            for season,windows in seasons.items()}
        for market,seasons in window_errors.items()}
    # Selection uses training season ONLY. Holdout never selects a window.
    window_selection={}
    for market,seasons in window_errors.items():
        training=seasons.get(TRAIN_SEASON,{})
        if not training:
            window_selection[market]={"status":"insufficient_training_data","selected_window":None}
            continue
        selected=min(training,key=lambda w:(training[w]["absolute_error"]/training[w]["n"],w))
        held=seasons.get(HOLDOUT_SEASON,{})
        selected_holdout=held.get(selected)
        baseline_holdout=held.get("all")
        # Split the training season chronologically; each candidate must improve
        # against all-prior in BOTH disjoint training periods.
        records=training_error_records[market]
        training_dates=sorted({day for day,_,_ in records})
        split_day=training_dates[len(training_dates)//2] if training_dates else None
        halves=[defaultdict(lambda:{"n":0,"error":0.0}) for _ in range(2)]
        for day,window,error in records:
            half=halves[0 if day<split_day else 1]
            half[window]["n"]+=1
            half[window]["error"]+=error
        stability=[]
        for half in halves:
            candidate=half.get(selected)
            baseline=half.get("all")
            enough=bool(candidate and baseline and candidate["n"]>=MIN_TRAIN_SPLIT_SAMPLES and baseline["n"]>=MIN_TRAIN_SPLIT_SAMPLES)
            stability.append({
                "samples":candidate["n"] if candidate else 0,
                "selected_mae":round(candidate["error"]/candidate["n"],4) if candidate and candidate["n"] else None,
                "baseline_mae":round(baseline["error"]/baseline["n"],4) if baseline and baseline["n"] else None,
                "passes":bool(enough and candidate["error"]/candidate["n"]<baseline["error"]/baseline["n"]),
            })
        stability_passed=all(part["passes"] for part in stability)
        improvement=(baseline_holdout["absolute_error"]-selected_holdout["absolute_error"])/baseline_holdout["absolute_error"] if selected_holdout and baseline_holdout and baseline_holdout["absolute_error"]>0 else None
        window_selection[market]={
            "status":"research_only",
            "holdout_improvement_fraction":round(improvement,6) if improvement is not None else None,
            "holdout_gate_passed":bool(improvement is not None and improvement>=MIN_HOLDOUT_RELATIVE_IMPROVEMENT and selected_holdout["n"]>=MIN_HOLDOUT_SAMPLES),
            "training_stability_passed":stability_passed,
            "training_chronological_halves":stability,
            "research_validation_gate_passed":bool(stability_passed and improvement is not None and improvement>=MIN_HOLDOUT_RELATIVE_IMPROVEMENT and selected_holdout["n"]>=MIN_HOLDOUT_SAMPLES),
            "rejection_reasons":(
                ([] if stability_passed else ["TRAINING_PERIOD_INSTABILITY_OR_INSUFFICIENT_SAMPLES"])
                + ([] if selected_holdout and selected_holdout["n"]>=MIN_HOLDOUT_SAMPLES else ["INSUFFICIENT_HOLDOUT_SAMPLES"])
                + ([] if improvement is not None and improvement>=MIN_HOLDOUT_RELATIVE_IMPROVEMENT else ["HOLDOUT_IMPROVEMENT_BELOW_ONE_PERCENT"])
            ),
            "bet_eligible":False,
            "training_season":TRAIN_SEASON,
            "holdout_season":HOLDOUT_SEASON,
            "selected_window":selected,
            "training_samples":training[selected]["n"],
            "holdout_samples":selected_holdout["n"] if selected_holdout else 0,
            "holdout_mae":round(selected_holdout["absolute_error"]/selected_holdout["n"],4) if selected_holdout else None,
            "holdout_all_prior_mae":round(baseline_holdout["absolute_error"]/baseline_holdout["n"],4) if baseline_holdout else None,
            "beats_holdout_all_prior":(selected_holdout["absolute_error"]<baseline_holdout["absolute_error"]) if selected_holdout and baseline_holdout else None,
        }
    return {"status":"research_only","promotion_approved":False,
        "fixed_reference_threshold_probability_research":brier_metrics,
        "fixed_reference_threshold_probability_by_season":season_probability_metrics,
        "fixed_reference_threshold_outcomes":threshold_metrics,
        "season_holdout_diagnostics":season_metrics,
        "window_comparison_by_season":window_diagnostics,
        "training_selected_window_holdout_audit":window_selection,
        "research_validation_policy":{"minimum_training_half_samples":MIN_TRAIN_SPLIT_SAMPLES,"minimum_holdout_samples":MIN_HOLDOUT_SAMPLES,"minimum_relative_holdout_mae_improvement":MIN_HOLDOUT_RELATIVE_IMPROVEMENT,"promotion_requires_external_betting_validation":True},
        "method":"strict-prior-date-walk-forward-player-rolling-mean",
        "minimum_prior_games":MIN_PRIOR,
        "markets":metrics,
        "warning":"Point-in-time sportsbook lines, injury/lineup context, calibration, joint SGP probability and independent validation are unavailable. Workload and opponent adjustments are not applied without verified point-in-time inputs. This is NOT a bet recommendation."}

def main():
    data=json.loads(SOURCE.read_text())
    result=evaluate(data)
    result["generated_at"]=datetime.now(timezone.utc).isoformat()
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"markets":result["markets"]}))

if __name__=="__main__":main()
