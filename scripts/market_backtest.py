"""Chronological evaluation of full-game margin and total predictions.
No historical bookmaker lines are present, so this is score/margin/total error
validation, NOT a historical ATS/totals betting ROI or EV backtest.
"""
import json,math,statistics
from pathlib import Path

def summarize(report):
    rows=report.get("results",[])
    if not rows:return {"sample_size":0,"status":"INSUFFICIENT_DATA"}
    margins=[(r["home_projected_points"]-r["away_projected_points"],r["actual_home_points"]-r["actual_away_points"]) for r in rows]
    totals=[(r["home_projected_points"]+r["away_projected_points"],r["actual_home_points"]+r["actual_away_points"]) for r in rows]
    def stats(pairs):
        errors=[a-b for a,b in pairs]
        return {"mae":statistics.mean(abs(e) for e in errors),"rmse":math.sqrt(statistics.mean(e*e for e in errors)),"bias":statistics.mean(errors)}
    return {"sample_size":len(rows),"status":"SCORE_ERRORS_ONLY_NO_HISTORICAL_LINES",
            "margin":stats(margins),"total":stats(totals),
            "ats_backtest":"UNAVAILABLE_NO_HISTORICAL_MARKET_LINES",
            "total_bet_backtest":"UNAVAILABLE_NO_HISTORICAL_MARKET_LINES",
            "verified_ev":"UNAVAILABLE_NO_HISTORICAL_MARKET_LINES"}
def main():
    for league in ("nfl","nba","nhl"):
        path=Path(f"feed/{league}_backtest.json")
        if not path.exists():raise RuntimeError(f"Missing {league} backtest")
        report=json.loads(path.read_text())
        result=summarize(report)
        result["league"]=league
        Path(f"feed/{league}_market_validation.json").write_text(json.dumps(result,indent=2)+"\n")
        print(league.upper(),"margin MAE:",result.get("margin",{}).get("mae"),"total MAE:",result.get("total",{}).get("mae"),"historical market ROI: unavailable")
if __name__=="__main__":main()
