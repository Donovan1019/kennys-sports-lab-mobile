"""Strictly historical NFL moneyline research; no claimed betting edge."""
import json,math
from datetime import datetime,timezone
from pathlib import Path
from scripts.connect_nfl_team_scores import team_parameters

def forecasts(games,market,asof):
    if asof.tzinfo is None:raise ValueError("Timezone-aware forecast clock required")
    cutoff=asof.astimezone(timezone.utc).date().isoformat()
    history=[g for g in games if isinstance(g.get("date"),str) and g["date"][:10]<cutoff]
    rows=[]
    for event in market.get("events",[]):
        home,away=event.get("home"),event.get("away")
        row={"event_id":event.get("event_id"),"home":home,"away":away,"asof":asof.isoformat(),"status":"unavailable","model_probability":None,"bet_eligible":False}
        if not home or not away:
            row["reason"]="Missing verified teams"
        else:
            h=team_parameters(history,home,asof.isoformat())
            a=team_parameters(history,away,asof.isoformat())
            if not h or not a:
                row["reason"]="Fewer than eight strictly prior-day games for a team"
            else:
                projected_home=(h["for_mean"]+a["against_mean"])/2
                projected_away=(a["for_mean"]+h["against_mean"])/2
                # Logistic-normal approximation to the difference of independent
                # team scores. Uncalibrated: research only, not an NFL win model.
                variance=(h["for_sd"]**2+a["against_sd"]**2+h["against_sd"]**2+a["for_sd"]**2)/2
                scale=max(1,math.sqrt(3*variance)/math.pi)
                z=max(-30,min(30,(projected_home-projected_away)/scale))
                p=1/(1+math.exp(-z))
                market_p=event.get("home_consensus_no_vig")
                row.update(status="experimental_research_only",model_probability=round(p,6),
                    model_market_difference_pp=round(100*(p-market_p),3) if type(market_p) in (int,float) and math.isfinite(market_p) else None,
                    projected_home_points=round(projected_home,2),projected_away_points=round(projected_away,2),
                    prior_home_games=h["games"],prior_away_games=a["games"],
                    reason="Uncalibrated score-difference approximation; QB, injury, weather and lineup uncertainty not verified; no betting eligibility")
        rows.append(row)
    return {"status":"experimental_research_only","asof":asof.isoformat(),"event_count":len(rows),"forecast_count":sum(r["model_probability"] is not None for r in rows),"events":rows}

def main():
    market=Path("feed/americanfootball_nfl_market_consensus.json")
    completed=Path("feed/nfl_completed_games.json")
    if not market.exists() or not completed.exists():
        print("NFL pregame research unavailable: missing consensus or verified completed scores")
        return
    now=datetime.now(timezone.utc)
    result=forecasts(json.loads(completed.read_text()).get("games",[]),json.loads(market.read_text()),now)
    Path("feed/americanfootball_nfl_pregame_research.json").write_text(json.dumps(result,indent=2)+"\n")
    print("NFL experimental pregame forecasts:",result["forecast_count"],"/",result["event_count"])
if __name__=="__main__":main()
