#!/usr/bin/env python3
"""Strict chronological NFL player-prop baseline audit. No sportsbook EV claims."""
import json, math, sys
from pathlib import Path

KEYS={"player_pass_yds":("Passing yards",{"QB"}),"player_reception_yds":("Receiving yards",{"WR","TE","RB"}),"player_rush_yds":("Rushing yards",{"RB","QB","WR"}),"player_receptions":("Receptions",{"WR","TE","RB"})}
def audit(data,min_train=5):
    if data.get("source")!="nflverse-stats-player-week" or not isinstance(data.get("players"),list):
        raise ValueError("Unverified NFL player stats feed")
    outcomes=[]
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
        by_market[market]={"status":"RESEARCH_ONLY","samples":len(rows),"brier":round(brier,6),"mean_predicted":round(sum(r["probability"] for r in rows)/len(rows),6),"observed_rate":round(sum(r["outcome"] for r in rows)/len(rows),6)}
    return {"status":"RESEARCH_ONLY","integrity":integrity,"participation_status":"UNVERIFIED","method":"chronological five-observed-stat-game mean threshold and smoothed empirical frequency; position-filtered, includes recorded zeros; NOT sportsbook-line calibration","leakage_policy":"Each prediction uses only earlier games for the same player and market","total_samples":len(outcomes),"markets":by_market,"limitations":"Recorded zero production is retained, but missing weekly rows and missing participation cannot be classified without snaps/injury evidence. Synthetic thresholds, not posted odds or real SGP prices; no opponent, joint-correlation, or market EV validation"}
if __name__=="__main__":
    src=Path(sys.argv[1] if len(sys.argv)>1 else "feed/nfl_player_stats.json")
    report=audit(json.loads(src.read_text()))
    print(json.dumps(report,indent=2))
