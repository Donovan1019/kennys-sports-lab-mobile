"""Strict walk-forward comparison of independent and correlated score Monte Carlo."""
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from scripts.connect_nfl_team_scores import team_parameters
from scripts.score_correlation_research import estimate, _date
from scripts.matchup_monte_carlo import simulate_game

def _metrics(rows):
    n=len(rows)
    if not n:
        return {"sample_size":0,"brier":None,"total_interval_80_coverage":None,
                "total_interval_80_width":None}
    return {"sample_size":n,
            "brier":round(sum((r["home_win_probability"]-r["home_won"])**2 for r in rows)/n,6),
            "total_interval_80_coverage":round(sum(r["total_interval_contains_actual"] for r in rows)/n,6),
            "total_interval_80_width":round(sum(r["total_interval_width"] for r in rows)/n,6)}

def compare(games, *, trials=10000, min_history=40, max_games=None):
    if type(trials) is not int or not 1000<=trials<=100000:
        raise ValueError("Invalid trial count")
    if max_games is not None and (type(max_games) is not int or max_games<1):
        raise ValueError("Invalid max_games")
    ordered=sorted((g for g in games if _date(g)),key=lambda g:_date(g))
    results=[]
    for i,g in enumerate(ordered):
        kickoff=_date(g)
        history=[x for x in ordered[:i] if _date(x)<kickoff]
        rho=estimate(history,kickoff,minimum=min_history)
        if rho["correlation"] is None:
            continue
        try:
            a=team_parameters(history,g["away"],g["date"])
            h=team_parameters(history,g["home"],g["date"])
            if not a or not h:
                continue
            am=(a["for_mean"]+h["against_mean"])/2
            hm=(h["for_mean"]+a["against_mean"])/2
            ads=math.sqrt((a["for_sd"]**2+h["against_sd"]**2)/2)
            hds=math.sqrt((h["for_sd"]**2+a["against_sd"]**2)/2)
            actual_total=g["away_score"]+g["home_score"]
            actual_winner=int(g["home_score"]>g["away_score"])
            if g["home_score"]==g["away_score"]:
                continue
        except (KeyError,ValueError,TypeError,ZeroDivisionError):
            continue
        models={}
        for name,correlation in (("independent",0),("correlated",rho["correlation"])):
            sims=simulate_game(am,hm,ads,hds,trials=trials,seed=1000+i)
            if correlation:
                sims=simulate_game(am,hm,ads,hds,trials=trials,seed=1000+i,score_correlation=correlation)
            decisive=[(away,home) for away,home in sims if abs(home-away)>1e-9]
            if not decisive:
                continue
            totals=sorted(away+home for away,home in sims)
            lo=totals[int(.1*(len(totals)-1))]
            hi=totals[int(.9*(len(totals)-1))]
            models[name]={"home_win_probability":sum(home>away for away,home in decisive)/len(decisive),
                          "home_won":actual_winner,"total_interval_contains_actual":int(lo<=actual_total<=hi),
                          "total_interval_width":hi-lo}
        if len(models)!=2:
            continue
        results.append({"date":g["date"],"event_id":g.get("event_id"),
                        "correlation":rho["correlation"],"history_size":rho["sample_size"],
                        "independent":models["independent"],"correlated":models["correlated"]})
        if max_games and len(results)>=max_games:
            break
    independent=_metrics([r["independent"] for r in results])
    correlated=_metrics([r["correlated"] for r in results])
    delta=round(correlated["brier"]-independent["brier"],6) if results else None
    return {"status":"research_only","method":"strict_walk_forward_same_games",
            "trials_per_game":trials,"sample_size":len(results),
            "independent":independent,"correlated":correlated,
            "correlated_minus_independent_brier":delta,
            "promotion_approved":False,
            "warning":"Score correlation is observational; game-total interval coverage and Brier alone do not establish betting edge or calibrated player-prop dependencies.",
            "results":results}

def main():
    for sport,league in (("americanfootball_nfl","nfl"),("basketball_nba","nba")):
        path=Path(f"feed/{league}_completed_games.json")
        if not path.exists():
            print(f"{sport}: no completed-game history")
            continue
        games=json.loads(path.read_text()).get("games",[])
        report=compare(games,trials=10000)
        Path(f"feed/{sport}_correlation_backtest.json").write_text(json.dumps(report,indent=2)+"\n")
        print(f"{sport}: walk-forward games={report['sample_size']} brier_delta={report['correlated_minus_independent_brier']}")
if __name__=="__main__":
    main()
