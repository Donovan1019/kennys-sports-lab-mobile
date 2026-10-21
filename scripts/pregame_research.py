"""Leakage-controlled, research-only pregame NBA/NHL forecasts.

Uses only completed games dated strictly before the UTC forecast date.
No live injuries, lineup or goalie confirmation; never publishes betting EV.
"""
import json
import math
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
from scripts.nhl_moneyline_model import home_moneyline_probability

def forecasts(sport, games, market, asof, nba_scale=None):
    if asof.tzinfo is None:raise ValueError("Timezone-aware asof required")
    cutoff=asof.astimezone(timezone.utc).date().isoformat()
    history=defaultdict(list)
    for g in games:
        try:
            day=g["date"][:10]
            if day>=cutoff:continue
            home,away=g["home"],g["away"]
            hs,aws=g["home_score"],g["away_score"]
            if not all(type(v) in (int,float) and math.isfinite(v) and v>=0 for v in (hs,aws)):continue
            history[home].append((day,hs,aws))
            history[away].append((day,aws,hs))
        except (KeyError,TypeError,ValueError):continue
    for team in history:history[team].sort(key=lambda x:x[0])
    out=[]
    for e in market.get("events",[]):
        home,away=e.get("home"),e.get("away")
        hh=history.get(home,[])[-40:]
        aa=history.get(away,[])[-40:]
        minimum=15 if sport=="basketball_nba" else 12
        row={"event_id":e.get("event_id"),"home":home,"away":away,"asof":asof.isoformat(),"status":"unavailable","bet_eligible":False,"model_probability":None,"model_market_difference_pp":None}
        if len(hh)<minimum or len(aa)<minimum:
            row["reason"]="Insufficient strictly prior-day team games or unmatched team names"
        elif sport=="basketball_nba" and not (type(nba_scale) in (int,float) and math.isfinite(nba_scale) and nba_scale>0):
            row["reason"]="Chronological NBA holdout calibration not verified"
        else:
            mean=lambda rows,i:sum(x[i] for x in rows)/len(rows)
            h=(mean(hh,1)+mean(aa,2))/2
            a=(mean(aa,1)+mean(hh,2))/2
            if sport=="basketball_nba":
                p=1/(1+math.exp(-((h+2-a)/nba_scale)))
            elif sport=="icehockey_nhl":
                p=home_moneyline_probability(max(.1,a),max(.1,h))
            else:raise ValueError("Unsupported sport")
            market_p=e.get("home_consensus_no_vig")
            row.update(status="experimental_research_only",model_probability=round(p,6),model_market_difference_pp=round(100*(p-market_p),3) if type(market_p) in (int,float) and math.isfinite(market_p) else None,reason="Unverified lineup/goalie and model-vs-market profitability; not bet eligible",prior_home_games=len(hh),prior_away_games=len(aa))
        out.append(row)
    return {"status":"experimental_research_only","asof":asof.isoformat(),"event_count":len(out),"forecast_count":sum(x["model_probability"] is not None for x in out),"events":out}

def main():
    asof=datetime.now(timezone.utc)
    nba_report=Path("feed/nba_backtest.json")
    scale=None
    if nba_report.exists():
        calibration=json.loads(nba_report.read_text()).get("chronological_holdout",{})
        if calibration.get("holdout_pass") is True:scale=calibration.get("logistic_scale")
    for sport,completed in (("basketball_nba","nba"),("icehockey_nhl","nhl")):
        market_path=Path(f"feed/{sport}_market_consensus.json")
        games_path=Path(f"feed/{completed}_completed_games.json")
        if not market_path.exists() or not games_path.exists():continue
        report=forecasts(sport,json.loads(games_path.read_text()).get("games",[]),json.loads(market_path.read_text()),asof,scale)
        Path(f"feed/{sport}_pregame_research.json").write_text(json.dumps(report,indent=2)+"\n")
        print(sport,"experimental pregame forecasts:",report["forecast_count"],"/",report["event_count"])
if __name__=="__main__":main()
