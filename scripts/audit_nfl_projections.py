#!/usr/bin/env python3
"""Leakage-safe expanding-history audit of the *unadjusted* NFL projection baseline.

Requires at least 8 prior observed games. No matchup/roster assumptions are backtested.
Does not validate sportsbook EV or probabilities. Exit nonzero on insufficient sample
or material systematic bias; never report a betting-ready model from this audit alone.
"""
import json, math, statistics, sys
from collections import defaultdict
from pathlib import Path

MARKETS = {
 "Passing Yards":"Passing yards","Passing TDs":"Passing touchdowns",
 "Rushing Yards":"Rushing yards","Receiving Yards":"Receiving yards",
 "Receptions":"Receptions","Rushing TDs":"Rushing touchdowns",
 "Receiving TDs":"Receiving touchdowns",
}
ROLES={"Passing Yards":{"QB"},"Passing TDs":{"QB"},"Rushing Yards":{"QB","RB","WR"},
       "Receiving Yards":{"RB","WR","TE"},"Receptions":{"RB","WR","TE"},
       "Rushing TDs":{"QB","RB","WR"},"Receiving TDs":{"RB","WR","TE"}}
def predict(history):
    def mean(x):return sum(x)/len(x)
    return .25*mean(history[:5])+.50*mean(history[:10])+.25*mean(history[:17])
def audit(payload):
    errors=defaultdict(list)
    counts=defaultdict(set)
    for p in payload.get("players",[]):
        role=str(p.get("position","")).upper()
        games=sorted((g for g in p.get("games",[]) if g.get("season") is not None and g.get("week") is not None and g.get("season_type") in ("REG","POST")),
                     key=lambda g:(int(g["season"]),int(g["week"]),g["season_type"]=="POST"))
        for market,key in MARKETS.items():
            if role not in ROLES[market]:continue
            observed=[(g,float(g["values"][key])) for g in games if key in g.get("values",{}) and g["values"][key] is not None and math.isfinite(float(g["values"][key])) and float(g["values"][key])>=0]
            for idx in range(8,len(observed)):
                g,actual=observed[idx]
                if int(g["season"])!=2026:continue
                history=[v for _,v in reversed(observed[:idx])]
                forecast=predict(history)
                errors[market].append((forecast-actual,abs(forecast-actual),forecast,actual))
                counts[market].add(str(p.get("id") or p.get("name")))
    results={}
    for market in MARKETS:
        rows=errors[market]
        n=len(rows)
        if not n:
            results[market]={"samples":0,"players":0,"status":"INSUFFICIENT_DATA"}
            continue
        bias=statistics.mean(x[0] for x in rows)
        mae=statistics.mean(x[1] for x in rows)
        rmse=math.sqrt(statistics.mean(x[0]**2 for x in rows))
        avg_actual=statistics.mean(x[3] for x in rows)
        results[market]={"samples":n,"players":len(counts[market]),"bias":round(bias,3),"mae":round(mae,3),"rmse":round(rmse,3),"mean_actual":round(avg_actual,3),
                         "bias_pct_of_actual":round(100*bias/avg_actual,2) if avg_actual>0 else None,
                         "status":"REVIEW" if n<50 or abs(bias)>max(.1*avg_actual, .1) else "BASELINE_CHECK_PASS"}
    return {"scope":"2026 actuals; prior-game-only NFL historical baseline","limitations":["Not a calibrated probability model","No sportsbook closing-line comparison","No verified current roster/availability","NFL market baseline only; no matchup factor"],"markets":results}


USAGE={"Passing Yards":"Pass Attempts","Rushing Yards":"Rush Attempts",
       "Receiving Yards":"Targets","Receptions":"Targets"}
def usage_prediction(prior, market):
    """Only observed earlier player games, never the outcome being predicted."""
    key=MARKETS[market];u=USAGE.get(market)
    if not u:return None
    paired=[]
    for g in reversed(prior):
        v=g.get("values",{})
        if key not in v or u not in v:continue
        try:y=float(v[key]);volume=float(v[u])
        except (TypeError,ValueError):continue
        if all(math.isfinite(x) and x>=0 for x in (y,volume)):paired.append((y,volume))
        if len(paired)>=10:break
    if len(paired)<8:return None
    baseline=predict([y for y,_ in paired])
    base_vol=statistics.mean(v for _,v in paired)
    total_vol=sum(v for _,v in paired)
    if base_vol<=0 or total_vol<=0:return None
    recent_vol=statistics.mean(v for _,v in paired[:5])
    opportunity=max(.8*base_vol,min(1.2*base_vol,.6*recent_vol+.4*base_vol))
    rate=sum(y for y,_ in paired)/total_vol
    return .75*baseline+.25*opportunity*rate
def compare(payload):
    records=defaultdict(list)
    for p in payload.get("players",[]):
        role=str(p.get("position","")).upper()
        games=sorted((g for g in p.get("games",[]) if g.get("season") is not None and g.get("week") is not None and g.get("season_type") in ("REG","POST")),key=lambda g:(int(g["season"]),int(g["week"]),g["season_type"]=="POST"))
        for market,key in MARKETS.items():
            if market not in USAGE or role not in ROLES[market]:continue
            for idx,g in enumerate(games):
                if int(g["season"])!=2026 or idx<8:continue
                try:actual=float(g["values"][key])
                except (KeyError,ValueError,TypeError):continue
                if not math.isfinite(actual) or actual<0:continue
                prior=games[:idx]
                paired=[float(x["values"][key]) for x in reversed(prior) if key in x.get("values",{}) and x["values"][key] is not None]
                if len(paired)<8:continue
                candidate=usage_prediction(prior,market)
                if candidate is None:continue
                baseline=predict(paired)
                records[market].append((baseline-actual,candidate-actual))
    out={}
    for market in USAGE:
        rows=records[market];n=len(rows)
        if not n:out[market]={"samples":0,"status":"INSUFFICIENT_DATA","promote":False};continue
        b_mae=statistics.mean(abs(x[0]) for x in rows)
        c_mae=statistics.mean(abs(x[1]) for x in rows)
        b_bias=statistics.mean(x[0] for x in rows)
        c_bias=statistics.mean(x[1] for x in rows)
        # Guard against overfitting: require >=100 matched forecasts and >=2% lower MAE,
        # while not materially increasing absolute systematic bias.
        promote=n>=100 and c_mae<=.98*b_mae and abs(c_bias)<=abs(b_bias)+.02*max(b_mae,1)
        out[market]={"samples":n,"baseline_mae":round(b_mae,3),"candidate_mae":round(c_mae,3),
                     "baseline_bias":round(b_bias,3),"candidate_bias":round(c_bias,3),
                     "mae_improvement_pct":round(100*(b_mae-c_mae)/b_mae,2) if b_mae else None,
                     "promote":promote,"status":"PASS" if promote else "REJECT"}
    return out


def coverage_audit(payload):
    """Strict out-of-sample 80% interval coverage, using prior games only."""
    rows=defaultdict(list)
    for p in payload.get("players",[]):
        role=str(p.get("position","")).upper()
        games=sorted((g for g in p.get("games",[]) if g.get("season") is not None and g.get("week") is not None and g.get("season_type") in ("REG","POST")),key=lambda g:(int(g["season"]),int(g["week"]),g["season_type"]=="POST"))
        for market,key in MARKETS.items():
            if role not in ROLES[market]:continue
            observed=[]
            for g in games:
                try:v=float(g.get("values",{})[key])
                except (KeyError,ValueError,TypeError):continue
                if math.isfinite(v) and v>=0:observed.append((g,v))
            for i in range(16,len(observed)):
                g,actual=observed[i]
                if int(g["season"])!=2026:continue
                history=[v for _,v in reversed(observed[:i])]
                center=predict(history)
                # Bootstrap the latest ten prior game deviations around their prior mean.
                prior10=history[:10]
                mean10=statistics.mean(prior10)
                outcomes=sorted(max(0,center+v-mean10) for v in prior10)
                lower=outcomes[0] # empirical 10th percentile for 10 samples
                upper=outcomes[8] # empirical 90th percentile for 10 samples
                rows[market].append((lower<=actual<=upper,upper-lower,actual))
    report={}
    for market in MARKETS:
        values=rows[market]
        n=len(values)
        if not n:
            report[market]={"samples":0,"status":"INSUFFICIENT_DATA"}
            continue
        coverage=statistics.mean(int(v[0]) for v in values)
        report[market]={"samples":n,"target_coverage":.8,"observed_coverage":round(coverage,4),
                        "mean_interval_width":round(statistics.mean(v[1] for v in values),3),
                        "status":"REVIEW" if n<100 or not .75<=coverage<=.85 else "COVERAGE_CHECK_PASS"}
    return report

def chronological_conformal_audit(payload):
    """Split 2026 chronologically; fit corrections on weeks <=4, test on >=5.

    Finite-sample split-conformal intervals target marginal 80% coverage only
    under exchangeability, which cannot be assumed for changing NFL roles.
    No tested outcome enters its own calibration set.
    """
    observations=defaultdict(list)
    for player in payload.get("players",[]):
        role=str(player.get("position","")).upper()
        games=sorted((g for g in player.get("games",[]) if g.get("season") is not None
                      and g.get("week") is not None and g.get("season_type") in ("REG","POST")),
                     key=lambda g:(int(g["season"]),int(g["week"]),g["season_type"]=="POST"))
        for market,key in MARKETS.items():
            if role not in ROLES[market]:continue
            valid=[]
            for g in games:
                try:value=float(g.get("values",{})[key])
                except (KeyError,ValueError,TypeError):continue
                if math.isfinite(value) and value>=0:valid.append((g,value))
            for idx in range(16,len(valid)):
                game,actual=valid[idx]
                if int(game["season"])!=2026 or game.get("season_type")!="REG":continue
                previous=[v for _,v in reversed(valid[:idx])]
                center=predict(previous)
                last10=previous[:10]
                average=statistics.mean(last10)
                simulated=sorted(max(0,center+v-average) for v in last10)
                observations[market].append((int(game["week"]),actual,simulated[0],simulated[8]))
    results={}
    for market in MARKETS:
        training=[r for r in observations[market] if r[0]<=4]
        testing=[r for r in observations[market] if r[0]>=5]
        if len(training)<30 or len(testing)<30:
            results[market]={"status":"INSUFFICIENT_DATA","calibration_samples":len(training),
                             "test_samples":len(testing),"ready":False}
            continue
        # Standard split conformal nonconformity, with ceil((n+1)*(1-alpha)).
        scores=sorted(max(low-y,y-high,0.0) for _,y,low,high in training)
        rank=math.ceil((len(scores)+1)*.8)
        correction=scores[rank-1] if rank<=len(scores) else math.inf
        base_hits=[low<=y<=high for _,y,low,high in testing]
        adjusted_hits=[max(0,low-correction)<=y<=high+correction
                       for _,y,low,high in testing]
        baseline=statistics.mean(base_hits)
        calibrated=statistics.mean(adjusted_hits)
        mean_width=statistics.mean(high-low+2*correction for _,_,low,high in testing)
        # Review thresholds are diagnostics, not sufficient betting approval.
        results[market]={"status":"COVERAGE_DIAGNOSTIC_PASS" if len(testing)>=100 and
                         .75<=calibrated<=.90 else "REVIEW",
                         "calibration_samples":len(training),"test_samples":len(testing),
                         "baseline_test_coverage":round(baseline,4),
                         "calibrated_test_coverage":round(calibrated,4),
                         "conformal_adjustment_each_side":round(correction,3),
                         "mean_calibrated_interval_width":round(mean_width,3),
                         "target_coverage":.8,"ready":False}
    return {"split":"2026 regular season weeks 1-4 calibration, weeks 5+ untouched test",
            "limitations":["Marginal coverage is not conditional player or game calibration",
                           "Nonstationary player usage can invalidate exchangeability",
                           "Historical outcomes alone cannot validate sportsbook edge"],
            "markets":results}


def independent_baseline_challenge(payload):
    """Paired, prior-game-only forecast benchmark; descriptive, no automatic promotion.

    Compares the existing 5/10/17 blend with the simple prior-10 mean on
    identical 2026 player-games. A lower error is necessary, not sufficient,
    for deployment: no sportsbook lines, independent tuning set, or odds here.
    """
    paired=defaultdict(list)
    for player in payload.get("players",[]):
        role=str(player.get("position","")).upper()
        games=sorted((g for g in player.get("games",[]) if g.get("season") is not None
                      and g.get("week") is not None and g.get("season_type") in ("REG","POST")),
                     key=lambda g:(int(g["season"]),int(g["week"]),g["season_type"]=="POST"))
        for market,key in MARKETS.items():
            if role not in ROLES[market]:continue
            observed=[]
            for game in games:
                try:value=float(game.get("values",{})[key])
                except (KeyError,TypeError,ValueError):continue
                if math.isfinite(value) and value>=0:observed.append((game,value))
            for idx in range(10,len(observed)):
                game,actual=observed[idx]
                if int(game["season"])!=2026 or game.get("season_type")!="REG":continue
                prior=[v for _,v in reversed(observed[:idx])]
                original=predict(prior)
                challenger=statistics.mean(prior[:10])
                paired[market].append((int(game["week"]),abs(original-actual),abs(challenger-actual)))
    result={}
    for market in MARKETS:
        rows=paired[market]
        n=len(rows)
        if not n:
            result[market]={"samples":0,"status":"INSUFFICIENT_DATA","promote":False}
            continue
        original_mae=statistics.mean(r[1] for r in rows)
        challenger_mae=statistics.mean(r[2] for r in rows)
        early=[r for r in rows if r[0]<=4]
        late=[r for r in rows if r[0]>=5]
        result[market]={
            "samples":n,
            "original_mae":round(original_mae,4),
            "simple_last10_mae":round(challenger_mae,4),
            "early_samples":len(early),"late_samples":len(late),
            "late_original_mae":round(statistics.mean(r[1] for r in late),4) if late else None,
            "late_simple_last10_mae":round(statistics.mean(r[2] for r in late),4) if late else None,
            "status":"CHALLENGER_LOWER_MAE_RESEARCH_ONLY" if challenger_mae<original_mae else "KEEP_EXISTING_BASELINE",
            "promote":False}
    return {"method":"paired historical player-games; no outcome used in its own forecast",
            "markets":result,"betting_ready":False,
            "limitations":["Same 2026 evaluation period is not independent model selection",
                           "No verified sportsbook price, player availability, or ROI",
                           "Do not promote solely on retrospective MAE"]}

def main():
    path=Path(sys.argv[1] if len(sys.argv)>1 else "feed/nfl_player_stats.json")
    report=Path(sys.argv[2] if len(sys.argv)>2 else "reports/nfl_projection_audit.json")
    payload=json.loads(path.read_text(encoding="utf-8"))
    result=audit(payload)
    result["usage_candidate_comparison"]=compare(payload)
    result["independent_baseline_challenge"]=independent_baseline_challenge(payload)
    result["simulation_80pct_coverage"]=coverage_audit(payload)
    result["chronological_conformal_80pct"]=chronological_conformal_audit(payload)
    coverage=result["simulation_80pct_coverage"]
    comparison=result["usage_candidate_comparison"]
    # Surface the markets whose nominal 80% simulated intervals under-cover.
    # These are not valid 80% probabilities until separately calibrated.
    result["uncertainty_calibration_priorities"]={
        "nominal_coverage":0.8,
        "markets":sorted([
            {"market":market,
             "samples":details.get("samples",0),
             "observed_coverage":details.get("observed_coverage"),
             "coverage_shortfall":round(.8-details["observed_coverage"],4),
             "priority":"HIGH" if details["observed_coverage"]<.7 else "REVIEW"}
            for market,details in coverage.items()
            if details.get("samples",0)>=50 and
               isinstance(details.get("observed_coverage"),(int,float)) and
               details["observed_coverage"]<.75
        ],key=lambda x:x["coverage_shortfall"],reverse=True),
        "action":"Block nominal 80% interval claims on undercovered markets; assess chronological conformal holdout before use",
        "betting_ready":False
    }
    result["betting_readiness"]={
        "status":"NOT_READY",
        "reason":"Unverified player roles/availability and sportsbook market matching; simulation calibration requires independently verified out-of-sample coverage",
        "markets":{market:{
            "simulation_coverage":coverage.get(market,{}).get("status","NOT_TESTED"),
            "chronological_conformal":result["chronological_conformal_80pct"]["markets"].get(market,{}).get("status","NOT_TESTED"),
            "candidate_promoted":bool(comparison.get(market,{}).get("promote",False)),
            "ready":False
        } for market in MARKETS}
    }
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
    if not any(v["samples"]>=50 for v in result["markets"].values()):
        raise SystemExit("INSUFFICIENT_DATA: no NFL market has 50 backtest observations")
if __name__=="__main__":main()
