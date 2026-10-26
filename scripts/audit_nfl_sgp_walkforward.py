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
                    outcomes.append({"market":market,"season":game["season"],"week":game["week"],"probability":probability,"outcome":outcome})
                history.append(value)
    by_market={}
    for market in KEYS:
        rows=[r for r in outcomes if r["market"]==market]
        if not rows:
            by_market[market]={"status":"INSUFFICIENT_DATA","samples":0}
            continue
        brier=sum((r["probability"]-r["outcome"])**2 for r in rows)/len(rows)
        observed=sum(r["outcome"] for r in rows)/len(rows)
        constant_brier=observed*(1-observed)
        skill=1-brier/constant_brier if constant_brier>0 else None
        by_market[market]={"status":"RESEARCH_ONLY","samples":len(rows),"brier":round(brier,6),"constant_rate_brier_in_sample":round(constant_brier,6),"skill_vs_in_sample_constant":round(skill,6) if skill is not None else None,"mean_predicted":round(sum(r["probability"] for r in rows)/len(rows),6),"observed_rate":round(observed,6)}
    return {"status":"RESEARCH_ONLY","integrity":integrity,"opportunity":opportunity,"participation_status":"OPPORTUNITY_CONFIRMED_ONLY","baseline_warning":"Constant-rate benchmark uses full evaluation outcomes (in-sample, look-ahead); diagnostic only, not a valid deployable baseline","method":"chronological five-opportunity-confirmed-game mean threshold and smoothed empirical frequency; position-filtered, retains zero outcomes when attempts/targets/carries > 0; NOT sportsbook-line calibration","leakage_policy":"Each prediction uses only earlier games for the same player and market","total_samples":len(outcomes),"markets":by_market,"limitations":"Opportunity-confirmed samples condition on observed attempts, targets or carries and exclude games with zero opportunity; this introduces post-game selection bias and is NOT a pregame hit probability. Snaps, routes, injury status and missing weekly rows are unverified. Synthetic thresholds, not posted odds or real SGP prices; no opponent, joint-correlation, or market EV validation"}
if __name__=="__main__":
    src=Path(sys.argv[1] if len(sys.argv)>1 else "feed/nfl_player_stats.json")
    report=audit(json.loads(src.read_text()))
    print(json.dumps(report,indent=2))
