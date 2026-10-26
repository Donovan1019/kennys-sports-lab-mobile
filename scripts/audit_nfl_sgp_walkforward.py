#!/usr/bin/env python3
"""Strict chronological NFL player-prop baseline audit. No sportsbook EV claims."""
import json, math, sys
from pathlib import Path

KEYS={"player_pass_yds":("Passing yards",{"QB"}),"player_reception_yds":("Receiving yards",{"WR","TE","RB"}),"player_rush_yds":("Rushing yards",{"RB","QB","WR"}),"player_receptions":("Receptions",{"WR","TE","RB"})}
OPPORTUNITY={"player_pass_yds":"Pass Attempts","player_reception_yds":"Targets","player_rush_yds":"Rush Attempts","player_receptions":"Targets"}
def audit(data,min_train=5):
    if data.get("source")!="nflverse-stats-player-week" or not isinstance(data.get("players"),list):
        raise ValueError("Unverified NFL player stats feed")
    outcomes=[]
    opportunity={"confirmed":0,"unverified":0,"zero_opportunity":0,"invalid":0}
    integrity={"missing_market_stat":0,"zero_market_stat":0,"negative_or_invalid":0,"position_excluded":0,"duplicate_player_weeks":0}
    for player in data["players"]:
        games=sorted((g for g in player.get("games",[]) if g.get("season_type")=="REG" and isinstance(g.get("season"),int) and isinstance(g.get("week"),int)),key=lambda g:(g["season"],g["week"]))
        for market,(key,positions) in KEYS.items():
            if player.get("position") not in positions:
                integrity["position_excluded"]+=len(games)
                continue
            history=[]
            past_outcomes=[]
            seen=set()
            for game in games:
                game_key=(game["season"],game["week"])
                if game_key in seen:
                    integrity["duplicate_player_weeks"]+=1
                    continue
                seen.add(game_key)
                value=game.get("values",{}).get(key)
                if value is None:
                    integrity["missing_market_stat"]+=1
                    continue
                if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
                    integrity["negative_or_invalid"]+=1
                    continue
                if value==0: integrity["zero_market_stat"]+=1
                count=game.get("values",{}).get(OPPORTUNITY[market])
                if count is None:
                    opportunity["unverified"]+=1
                    continue
                if isinstance(count,bool) or not isinstance(count,(int,float)) or not math.isfinite(count) or count<0:
                    opportunity["invalid"]+=1
                    continue
                if count==0:
                    opportunity["zero_opportunity"]+=1
                    continue
                opportunity["confirmed"]+=1
                if len(history)>=min_train:
                    threshold=sum(history[-5:])/5
                    probability=(sum(v>threshold for v in history[-5:])+1)/7
                    outcome=int(value>threshold)
                    # Only prior scored events inform the rolling benchmark; never this outcome.
                    baseline=(sum(past_outcomes[-10:])+1)/(len(past_outcomes[-10:])+2)
                    outcomes.append({"market":market,"season":game["season"],"week":game["week"],"probability":probability,"rolling_baseline":baseline,"outcome":outcome})
                    past_outcomes.append(outcome)
                history.append(value)
    # Prequential calibration: fit only on earlier calendar weeks, never same-week results.
    # Conservative shrinkage toward raw forecasts prevents unstable tiny-history fits.
    ordered=sorted(set((r["season"],r["week"]) for r in outcomes))
    prior_by_market={market:[] for market in KEYS}
    by_week={}
    for r in outcomes:
        by_week.setdefault((r["season"],r["week"]),[]).append(r)
    for week in ordered:
        for r in by_week[week]:
            prior=prior_by_market[r["market"]]
            if len(prior)>=100:
                bias=sum(x["outcome"]-x["probability"] for x in prior)/len(prior)
                r["calibrated_probability"]=max(0.01,min(0.99,r["probability"]+bias*len(prior)/(len(prior)+200)))
            else:
                r["calibrated_probability"]=r["probability"]
            r["calibration_training_samples"]=len(prior)
        for r in by_week[week]:
            prior_by_market[r["market"]].append(r)
    by_market={}
    for market in KEYS:
        rows=[r for r in outcomes if r["market"]==market]
        if not rows:
            by_market[market]={"status":"INSUFFICIENT_DATA","samples":0}
            continue
        brier=sum((r["probability"]-r["outcome"])**2 for r in rows)/len(rows)
        calibrated_brier=sum((r["calibrated_probability"]-r["outcome"])**2 for r in rows)/len(rows)
        calibrated_ece=0.0
        for lower in range(0,100,10):
            selected=[r for r in rows if lower/100<=r["calibrated_probability"]<(lower+10)/100 or (lower==90 and r["calibrated_probability"]==1)]
            if selected:
                calibrated_ece+=len(selected)/len(rows)*abs(sum(r["calibrated_probability"] for r in selected)/len(selected)-sum(r["outcome"] for r in selected)/len(selected))
        rolling_brier=sum((r["rolling_baseline"]-r["outcome"])**2 for r in rows)/len(rows)
        rolling_skill=1-brier/rolling_brier if rolling_brier>0 else None
        # Reliability bins are descriptive only: never fit a calibrator on held-out outcomes.
        bins=[]
        ece=0.0
        for lower in range(0,100,10):
            selected=[r for r in rows if lower/100<=r["probability"]<(lower+10)/100 or (lower==90 and r["probability"]==1)]
            if not selected: continue
            predicted=sum(r["probability"] for r in selected)/len(selected)
            actual=sum(r["outcome"] for r in selected)/len(selected)
            ece+=len(selected)/len(rows)*abs(predicted-actual)
            bins.append({"lower":lower/100,"upper":(lower+10)/100,"samples":len(selected),"predicted":round(predicted,6),"observed":round(actual,6)})
        observed=sum(r["outcome"] for r in rows)/len(rows)
        constant_brier=observed*(1-observed)
        skill=1-brier/constant_brier if constant_brier>0 else None
        by_market[market]={"status":"RESEARCH_ONLY","samples":len(rows),"brier":round(brier,6),"prequential_calibrated_brier":round(calibrated_brier,6),"prequential_calibrated_ece":round(calibrated_ece,6),"prequential_calibration_samples":sum(r["calibration_training_samples"]>=100 for r in rows),"reliability_bins":bins,"expected_calibration_error":round(ece,6),"chronological_rolling_brier":round(rolling_brier,6),"skill_vs_chronological_rolling":round(rolling_skill,6) if rolling_skill is not None else None,"constant_rate_brier_in_sample":round(constant_brier,6),"skill_vs_in_sample_constant":round(skill,6) if skill is not None else None,"mean_predicted":round(sum(r["probability"] for r in rows)/len(rows),6),"observed_rate":round(observed,6)}
    return {"status":"RESEARCH_ONLY","integrity":integrity,"opportunity":opportunity,"participation_status":"OPPORTUNITY_CONFIRMED_ONLY","bet_eligibility":"BLOCKED","calibration_status":"PREQUENTIAL_RESEARCH_ONLY","calibration_warning":"Calendar-week prequential additive bias correction uses only previous weeks per market, with minimum 100 observations and shrinkage; diagnostic comparison, not sportsbook probability calibration.","baseline_warning":"Chronological rolling baseline uses only prior scored player-market outcomes (up to 10, Laplace-smoothed); constant-rate benchmark uses full evaluation outcomes (in-sample, look-ahead) and is diagnostic only. Both use postgame opportunity-conditioned samples and synthetic thresholds.","method":"chronological five-opportunity-confirmed-game mean threshold and smoothed empirical frequency; position-filtered, retains zero outcomes when attempts/targets/carries > 0; NOT sportsbook-line calibration","leakage_policy":"Each prediction uses only earlier games for the same player and market","total_samples":len(outcomes),"markets":by_market,"limitations":"Opportunity-confirmed samples condition on observed attempts, targets or carries and exclude games with zero opportunity; this introduces post-game selection bias and is NOT a pregame hit probability. Snaps, routes, injury status and missing weekly rows are unverified. Synthetic thresholds, not posted odds or real SGP prices; no opponent, joint-correlation, or market EV validation"}
if __name__=="__main__":
    src=Path(sys.argv[1] if len(sys.argv)>1 else "feed/nfl_player_stats.json")
    report=audit(json.loads(src.read_text()))
    print(json.dumps(report,indent=2))
