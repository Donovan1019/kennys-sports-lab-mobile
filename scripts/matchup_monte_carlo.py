"""Experimental independent game-score Monte Carlo. No sportsbook odds used as model inputs."""
import json,math,random
from datetime import datetime,timezone
from pathlib import Path

def probability_and_ev(p,american):
    if not 0<p<1 or not isinstance(american,(int,float)) or -100<american<100:
        raise ValueError("Invalid model probability or odds")
    return p*(american/100 if american>0 else 100/-american)-(1-p)

def simulate_game(away_mean,home_mean,away_sd,home_sd,*,trials=10000,seed=42):
    values=(away_mean,home_mean,away_sd,home_sd)
    if any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in values) or min(away_mean,home_mean)<0 or min(away_sd,home_sd)<=0 or not 1000<=trials<=100000:
        raise ValueError("Invalid simulation configuration")
    rng=random.Random(seed)
    return [(max(0,rng.gauss(away_mean,away_sd)),max(0,rng.gauss(home_mean,home_sd))) for _ in range(trials)]

def probability(scores,market,selection,point,away,home):
    if market not in ("h2h","spreads","totals"):raise ValueError("Unsupported market")
    if market=="totals" and selection.lower() not in ("over","under"):raise ValueError("Invalid total")
    if market in ("spreads","totals") and not isinstance(point,(int,float)):raise ValueError("Missing line")
    if market in ("h2h","spreads") and selection not in (away,home):raise ValueError("Invalid team")
    hits=pushes=0
    for a,h in scores:
        if market=="h2h":delta=a-h if selection==away else h-a
        elif market=="spreads":delta=(a-h if selection==away else h-a)+point
        else:delta=(a+h-point)*(1 if selection.lower()=="over" else -1)
        if abs(delta)<1e-9:pushes+=1
        elif delta>0:hits+=1
    return {"wins":hits,"pushes":pushes,"losses":len(scores)-hits-pushes,"probability":hits/(len(scores)-pushes) if len(scores)>pushes else None}

def build_forecasts(inputs,odds):
    if inputs.get("source")!="verified-independent-team-scoring" or not isinstance(inputs.get("games"),list):raise ValueError("Independent game scoring inputs required")
    if odds.get("source")!="the-odds-api-v4":raise ValueError("Verified odds required")
    results=[]
    for game in inputs["games"]:
        if game.get("validated") is not True or game.get("sample_size",0)<8:continue
        try:
            from scripts.sport_simulation import simulate_sport
            scores=simulate_sport(game["sport"],game["away_mean"],game["home_mean"],game["away_sd"],game["home_sd"],seed=42)
        except (KeyError,TypeError,ValueError):continue
        for row in odds.get("odds",[]):
            if row.get("event_id")!=game.get("event_id") or row.get("sport")!=game.get("sport"):continue
            try:
                r=probability(scores,row["market"],row["selection"],row.get("point"),game["away_team"],game["home_team"])
                if r["probability"] is None:continue
                results.append({"sport":game["sport"],"event_id":game["event_id"],"market":row["market"],"selection":row["selection"],"point":row.get("point"),"model_probability":r["probability"],"simulations":len(scores),"pushes":r["pushes"],"model_version":"independent-scoring-mc-v1","input_timestamp":game["as_of"],"status":"experimental","is_forecast":True,"sample_size":game["sample_size"],"bookmaker":row.get("bookmaker"),"ev_per_unit":probability_and_ev(r["probability"],row["price"])})
            except (KeyError,ValueError,TypeError):continue
    return {"schema_version":1,"generated_at":datetime.now(timezone.utc).isoformat(),"model_status":"experimental-not-calibrated","predictions":results}
